import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "review_flow.py"
spec = importlib.util.spec_from_file_location("review_flow", SCRIPT)
flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flow)

class FlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "app.py").write_text("answer = 42\n", encoding="utf-8")
        self.run = self.root / "run"

    def cmd(self, *args, ok=True):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = flow.main(["--run-dir", str(self.run), *args])
        self.assertEqual(result, 0 if ok else 2, args)
        return result

    def state(self):
        return flow.read_json(self.run / "state.json")

    def file(self, name, value):
        p = self.root / name
        p.write_text(json.dumps(value), encoding="utf-8")
        return str(p)

    def init(self, mode="adaptive", *extra):
        self.cmd("init", "--project", str(self.project), "--task", "Review answer", "--scope", "app.py", "--mode", mode, *extra)

    def judge(self, checkpoint="scope", *extra, ok=True):
        self.cmd("judge", "--checkpoint", checkpoint, "--decision", "proceed", "--execution", "deterministic", "--reason", "bounded fixture", *extra, ok=ok)

    def check(self, code="print('verified')", ok=True, *extra):
        self.cmd("check", "--argv-json", json.dumps([sys.executable, "-c", code]), *extra, ok=ok)

    def ready(self, mode="adaptive"):
        self.init(mode)
        self.judge()
        self.check()
        self.cmd("risk", "--level", "low", "--reason", "fixture only")
        if mode == "joint":
            self.judge("review")

    def review(self, issues=None, fixed=None, reviewer="reviewer-a", ok=True, snapshot=None):
        r = {"snapshot": snapshot or self.state()["snapshot"], "reviewer": reviewer,
             "independent": True, "dimensions": sorted(flow.DIMENSIONS), "findings": issues or [],
             "verified_fixed": fixed or []}
        self.cmd("review", "--input", self.file("review.json", r), ok=ok)

    def issue(self):
        return {"id": "R1", "tag": "Important", "file": "app.py", "line": 1,
                "evidence": "fixture boundary", "reason": "required behavior absent"}

    def test_happy_modes(self):
        for mode in ("serial", "joint", "adaptive"):
            with self.subTest(mode=mode):
                if self.run.exists():
                    self.run = self.root / ("run-" + mode)
                self.ready(mode)
                self.review()
                if mode == "joint":
                    self.cmd("close", ok=False)
                    self.judge("close")
                self.cmd("close")
                self.assertTrue(self.state()["closed"])

    def test_no_forward_bypass(self):
        self.init()
        for action in ("close",):
            self.cmd(action, ok=False)
        self.cmd("route", "--target", "review", "--reason", "skip checks", ok=False)
        self.assertEqual(self.state()["checks"], [])

    def test_changed_content_invalidates(self):
        self.ready()
        self.review()
        (self.project / "app.py").write_text("answer = 43\n")
        self.cmd("close", ok=False)
        s = self.state()
        self.assertEqual(s["round"], 2)
        self.assertEqual(s["checks"], [])
        self.assertEqual(s["reports"], [])

    def test_owner_change_invalidates(self):
        (self.project / "AGENTS.md").write_text("Use fixture checks\n")
        self.ready()
        (self.project / "AGENTS.md").write_text("New convention\n")
        self.cmd("status")
        self.assertIsNone(self.state()["risk"])

    def test_stale_report(self):
        self.ready()
        self.review(snapshot="old-hash", ok=False)
        self.assertFalse(self.state()["reports"])

    def test_closed_run_does_not_reopen_on_source_change(self):
        self.ready()
        self.review()
        self.cmd("close")
        original = self.state()
        (self.project / "app.py").write_text("answer = 44\n")
        self.cmd("status")
        self.assertEqual(self.state(), original)
        self.judge(ok=False)
        self.assertEqual(self.state(), original)

    def test_important_cannot_disappear_via_route(self):
        self.ready()
        self.review([self.issue()])
        self.cmd("close", ok=False)
        self.cmd("route", "--target", "review", "--reason", "second look")
        self.judge()
        self.review(reviewer="reviewer-b")
        self.cmd("close", ok=False)
        self.assertIn("R1", self.state()["issues"])

    def test_important_id_cannot_overwrite_prior_obligation(self):
        self.ready()
        self.review([self.issue()])
        original = self.state()["issues"]["R1"]
        self.cmd("route", "--target", "review", "--reason", "new pass")
        self.judge()
        changed = self.issue()
        changed["reason"] = "different problem using the same id"
        self.review([changed], reviewer="reviewer-b", ok=False)
        self.assertEqual(self.state()["issues"]["R1"], original)

    def test_review_budget_also_counts_unchanged_content(self):
        self.ready()
        self.review()
        for index in (2, 3):
            self.cmd("route", "--target", "review", "--reason", "another pass")
            self.judge()
            self.review(reviewer="reviewer-" + str(index))
            self.assertEqual(self.state()["round"], index)
        self.cmd("route", "--target", "review", "--reason", "fourth pass", ok=False)
        self.assertTrue(self.state()["reports"])

    def test_fix_requires_changed_content_and_independent_confirmation(self):
        self.ready()
        self.review([self.issue()])
        d = self.file("decisions.json", {"R1": {"action": "fixed", "reason": "claim", "evidence": "claim"}})
        self.cmd("adjudicate", "--input", d, ok=False)
        (self.project / "app.py").write_text("answer = 43\n")
        self.cmd("status")
        self.judge()
        self.check()
        self.cmd("risk", "--level", "low", "--reason", "bounded")
        self.review(fixed=[{"id": "R1", "evidence": "new behavior verified"}], reviewer="reviewer-b")
        self.cmd("adjudicate", "--input", d)
        self.cmd("close")

    def test_rejected_finding_needs_evidence(self):
        self.ready()
        self.review([self.issue()])
        p = self.file("decisions.json", {"R1": {"action": "reject", "reason": "intentional", "evidence": ""}})
        self.cmd("adjudicate", "--input", p, ok=False)
        self.cmd("close", ok=False)

    def test_adjudication_route_requires_new_disposition(self):
        self.ready()
        self.review([self.issue()])
        p = self.file("decisions.json", {"R1": {"action": "reject", "reason": "not introduced", "evidence": "baseline record"}})
        self.cmd("adjudicate", "--input", p)
        self.cmd("route", "--target", "adjudication", "--reason", "recheck attribution")
        self.judge()
        self.assertIsNone(self.state()["issues"]["R1"]["resolution"])
        self.cmd("close", ok=False)
        self.cmd("adjudicate", "--input", p)
        self.cmd("close")

    def test_reused_nit_id_cannot_become_important(self):
        self.ready()
        nit = dict(self.issue(), tag="Nit")
        self.review([nit])
        self.cmd("route", "--target", "review", "--reason", "new pass")
        self.judge()
        self.review([self.issue()], reviewer="reviewer-b", ok=False)

    def test_high_risk_two_distinct_human_attestations(self):
        self.ready()
        self.cmd("risk", "--level", "high", "--reason", "sensitive fixture")
        self.review()
        self.cmd("close", ok=False)
        def approve(actor, snapshot=None, ok=True):
            p = self.file("approval.json", {"kind": "human", "actor": actor,
                          "snapshot": snapshot or self.state()["snapshot"], "evidence": "test-only attestation"})
            self.cmd("approve", "--input", p, ok=ok)
        approve("human-a")
        approve("human-a", ok=False)
        approve("human-b", snapshot="stale", ok=False)
        self.cmd("close", ok=False)
        approve("human-b")
        self.cmd("close")

    def test_sensitive_low_still_requires_human(self):
        self.ready()
        self.cmd("risk", "--level", "low", "--sensitive", "--reason", "release docs affect decisions")
        self.review()
        self.cmd("close", ok=False)

    def test_failed_execution_requires_attribution(self):
        self.init()
        self.judge()
        self.check("sys.exit(1)".replace("sys.", "__import__('sys')."), ok=False)
        self.judge(ok=False)
        self.judge("scope", "--failure-class", "parameters")
        self.cmd("route", "--target", "verification", "--reason", "corrected input")
        self.judge()
        self.check()
        self.cmd("risk", "--level", "low", "--reason", "corrected check")

    def test_denied_is_terminal(self):
        self.init()
        self.judge()
        self.check("raise PermissionError('fixture denial')", ok=False)
        self.judge("scope", "--failure-class", "denied", ok=False)
        self.cmd("judge", "--decision", "handoff", "--execution", "agent", "--reason", "permission denied",
                 "--failure-class", "denied")
        self.cmd("route", "--target", "judgment", "--reason", "bypass", ok=False)

    def test_missing_owner_no_guess(self):
        self.init()
        self.judge("scope", "--owner", str(self.root / "missing.md"), ok=False)

    def test_timeout_persisted(self):
        self.init()
        self.judge()
        self.check("import time;time.sleep(2)", False, "--timeout", "1")
        self.assertTrue(self.state()["checks"][0]["timeout"])

    def test_log_tampering_blocks_close(self):
        self.ready()
        self.review()
        (self.run / self.state()["checks"][0]["log"]).write_text("tampered")
        self.cmd("close", ok=False)

    def test_content_budget_exhausted(self):
        self.init("adaptive", "--max-rounds", "1")
        (self.project / "app.py").unlink()
        self.cmd("status", ok=False)
        self.assertEqual(self.state()["round"], 1)

    def test_bad_paths_and_lock(self):
        self.cmd("init", "--project", str(self.project), "--task", "escape", "--scope", "../outside", ok=False)
        self.init()
        (self.run / ".lock").write_text("other owner")
        self.cmd("status", ok=False)
        self.assertTrue((self.run / ".lock").exists())

    def test_reviewer_coverage_and_duplicates(self):
        self.ready()
        r = {"snapshot": self.state()["snapshot"], "reviewer": "a", "independent": True,
             "dimensions": ["correctness"], "findings": []}
        self.cmd("review", "--input", self.file("partial.json", r))
        self.cmd("close", ok=False)
        self.review(reviewer="a", ok=False)
        r["reviewer"] = "b"
        r["dimensions"] = ["security", "end-to-end", "conventions"]
        self.cmd("review", "--input", self.file("partial.json", r))
        self.cmd("close")

if __name__ == "__main__":
    unittest.main(verbosity=2)
