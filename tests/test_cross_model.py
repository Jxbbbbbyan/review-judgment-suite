import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("review_bus", ROOT / "optional/cross_model/review_bus.py")
bus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bus)

class CrossModelTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "app.py").write_text("answer = 42\n")
        self.run = self.root / "core-run"
        self.flow = bus.core()
        self.flow_cmd("init", "--project", str(self.project), "--task", "Review answer", "--scope", "app.py")
        self.flow_cmd("judge", "--decision", "proceed", "--execution", "deterministic", "--reason", "bounded")
        self.flow_cmd("check", "--argv-json", json.dumps([sys.executable, "-c", "assert 6*7==42"]))
        self.flow_cmd("risk", "--level", "low", "--reason", "synthetic fixture")
        self.context = self.write("context.json", {"intent": "Review answer", "diff": "+answer = 42", "conventions": "bounded fixture"})
        self.config_file = self.root / "routes.json"
        self.cfg = {"schema": 1, "enabled": True, "spool_root": "mailbox",
                    "routes": [{"source": "dsh", "target": "codex"}, {"source": "codex", "target": "grok-bot"}],
                    "workers": {"codex": {"model": "review-model", "cwd": str(self.root),
                                "argv": [sys.executable, str(ROOT / "optional/cross_model/demo_worker.py")]}}}
        self.save_config()
        self.reqfile = self.root / "request.json"
        self.cmd("create", "--run-dir", str(self.run), "--context", self.context,
                 "--source-host", "dsh", "--source-model", "developer-model",
                 "--target-host", "codex", "--target-model", "review-model", "--output", str(self.reqfile))
        self.req = bus.load(self.reqfile)

    def write(self, name, value):
        p = self.root / name
        p.write_text(json.dumps(value), encoding="utf-8")
        return str(p)

    def save_config(self):
        self.config_file.write_text(json.dumps(self.cfg), encoding="utf-8")

    def flow_cmd(self, *args, ok=True, run=None):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = self.flow.main(["--run-dir", str(run or self.run), *args])
        self.assertEqual(code, 0 if ok else 2)

    def cmd(self, *args, ok=True):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = bus.main(list(args))
        self.assertEqual(code, 0 if ok else 2, args)

    def send(self, ok=True):
        self.cmd("send", "--request", str(self.reqfile), "--config", str(self.config_file), "--enable", "--confirm-share", ok=ok)

    def gateway(self, ok=True):
        self.cmd("gateway", "--request-id", self.req["request_id"], "--target", "codex", "--config", str(self.config_file), "--enable", ok=ok)

    def work(self, ok=True, timeout=None):
        argv = ["work", "--request-id", self.req["request_id"], "--target", "codex", "--config", str(self.config_file), "--enable"]
        if timeout: argv += ["--timeout", str(timeout)]
        self.cmd(*argv, ok=ok)

    def roundtrip(self):
        self.send(); self.gateway(); self.work()
        out = self.root / "response.json"
        self.cmd("poll", "--config", str(self.config_file), "--request", str(self.reqfile), "--enable", "--output", str(out))
        return out

    def test_full_local_round_trip_and_core_import(self):
        out = self.roundtrip()
        self.cmd("import", "--run-dir", str(self.run), "--request", str(self.reqfile), "--response", str(out), "--enable")
        state = self.flow.read_json(self.run / "state.json")
        self.assertEqual(len(state["reports"]), 1)
        self.assertFalse(state["closed"])
        self.assertIn("codex/review-model", state["reports"][0]["reviewer"])

    def test_default_disabled_and_explicit_enable(self):
        self.cfg["enabled"] = False; self.save_config()
        self.send(ok=False)
        self.assertFalse((self.root / "mailbox").exists())
        self.cfg["enabled"] = True; self.save_config()
        self.cmd("send", "--request", str(self.reqfile), "--config", str(self.config_file), "--confirm-share", ok=False)

    def test_share_confirmation_required(self):
        self.cmd("send", "--request", str(self.reqfile), "--config", str(self.config_file), "--enable", ok=False)

    def test_duplicate_send_gateway_worker_and_import_refused(self):
        out = self.roundtrip()
        self.send(ok=False); self.gateway(ok=False); self.work(ok=False)
        args = ("import", "--run-dir", str(self.run), "--request", str(self.reqfile), "--response", str(out), "--enable")
        self.cmd(*args); self.cmd(*args, ok=False)

    def test_wrong_route_or_model_refused(self):
        self.cfg["routes"] = []; self.save_config(); self.send(ok=False)
        self.cfg["routes"] = [{"source": "dsh", "target": "codex"}]
        self.cfg["workers"]["codex"]["model"] = "another-model"; self.save_config()
        self.send(); self.gateway(); self.work(ok=False)

    def test_request_commands_and_digest_tampering_refused(self):
        r = dict(self.req, argv=["not-executed"])
        self.write("request.json", r); self.send(ok=False)
        r = dict(self.req); r["context"] = dict(r["context"], diff="changed")
        self.write("request.json", r); self.send(ok=False)

    def test_response_correlation_and_target_refused(self):
        out = self.roundtrip()
        response = bus.load(out); response["request_id"] = "wrong"
        self.write("response.json", response)
        self.cmd("import", "--run-dir", str(self.run), "--request", str(self.reqfile), "--response", str(out), "--enable", ok=False)

    def test_stale_content_and_different_run_refused(self):
        out = self.roundtrip()
        args = ("import", "--run-dir", str(self.run), "--request", str(self.reqfile), "--response", str(out), "--enable")
        (self.project / "app.py").write_text("answer = 43\n")
        self.cmd(*args, ok=False)
        (self.project / "app.py").write_text("answer = 42\n")
        other = self.root / "another-run"
        self.flow_cmd("init", "--project", str(self.project), "--task", "A different request", "--scope", "app.py", run=other)
        self.cmd("import", "--run-dir", str(other), "--request", str(self.reqfile), "--response", str(out), "--enable", ok=False)

    def test_timeout_retains_receipt_and_prevents_automatic_retry(self):
        self.cfg["workers"]["codex"]["argv"] = [sys.executable, "-c", "import time;time.sleep(3)"]
        self.save_config(); self.send(); self.gateway(); self.work(ok=False, timeout=1)
        self.work(ok=False)
        self.assertTrue((self.root / "mailbox/work/codex" / (self.req["request_id"] + ".started.json")).exists())

    def test_receiver_manual_report_return(self):
        self.send(); self.gateway()
        received = self.root / "received.json"
        self.cmd("take", "--config", str(self.config_file), "--target", "codex", "--request-id", self.req["request_id"], "--enable", "--output", str(received))
        report = {"snapshot": self.req["snapshot"], "reviewer": "external-reviewer", "independent": True,
                  "dimensions": sorted(bus.DIMENSIONS), "findings": []}
        f = self.write("manual-report.json", report)
        self.cmd("respond", "--config", str(self.config_file), "--request", str(received), "--report", f, "--enable")
        self.work(ok=False)

    def test_same_declared_model_rejected(self):
        r = dict(self.req); r["target"] = dict(r["target"], model="DEVELOPER-MODEL")
        r["digest"] = bus.checksum({k: v for k, v in r.items() if k != "digest"})
        self.write("request.json", r); self.send(ok=False)

    def test_path_and_oversize_or_duplicate_json_refused(self):
        self.cmd("gateway", "--config", str(self.config_file), "--request-id", "../escape", "--target", "codex", "--enable", ok=False)
        self.reqfile.write_text('{"schema":1,"schema":2}')
        self.send(ok=False)
        self.reqfile.write_text('x' * (bus.LIMIT + 1))
        self.send(ok=False)

    def test_utf8_worker_ignores_legacy_console_encoding(self):
        r = dict(self.req); r["context"] = dict(r["context"], intent="审查中文更改")
        result = subprocess.run([sys.executable, str(ROOT / "optional/cross_model/demo_worker.py")],
                                input=json.dumps(r, ensure_ascii=False).encode("utf-8"), capture_output=True,
                                env=dict(os.environ, PYTHONUTF8="0", PYTHONIOENCODING="cp936"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["snapshot"], r["snapshot"])

    def test_release_excludes_optional_runtime_even_when_gitignored(self):
        spec = importlib.util.spec_from_file_location("release_under_test", ROOT / "scripts/build_release.py")
        builder = importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
        builder.ROOT = self.root
        public = self.root / "optional/cross_model/demo_worker.py"
        public.parent.mkdir(parents=True); public.write_text("print('fixture')\n")
        private_config = self.root / "optional/cross_model/routes.local.json"
        private_config.write_text('{"private":"sentinel-do-not-publish"}')
        payload = self.root / "optional/private-review-mailbox/requests/codex/private.json"
        payload.parent.mkdir(parents=True); payload.write_text('{"diff":"sentinel-do-not-publish"}')
        emitted = {p.relative_to(self.root).as_posix() for p in builder.files()}
        self.assertEqual(emitted, {"optional/cross_model/demo_worker.py"})

    def test_codex_to_grok_bot_route(self):
        r = dict(self.req)
        r["source"] = {"host": "codex", "model": "developer-model"}
        r["target"] = {"host": "grok-bot", "model": "review-model"}
        r["digest"] = bus.checksum({k: v for k, v in r.items() if k != "digest"})
        self.write("request.json", r)
        self.cfg["workers"]["grok-bot"] = self.cfg["workers"]["codex"]
        self.save_config(); self.send()
        for action in ("gateway", "work"):
            self.cmd(action, "--config", str(self.config_file), "--target", "grok-bot", "--request-id", r["request_id"], "--enable")
        out = self.root / "grok-response.json"
        self.cmd("poll", "--config", str(self.config_file), "--request", str(self.reqfile), "--output", str(out), "--enable")
        self.assertEqual(bus.load(out)["reviewer_host"]["host"], "grok-bot")

    def test_external_important_still_blocks_core_closure(self):
        self.send(); self.gateway()
        report = {"snapshot": self.req["snapshot"], "reviewer": "other-model-reviewer", "independent": True,
                  "dimensions": sorted(bus.DIMENSIONS), "findings": [{"id": "cross-1", "tag": "Important",
                  "file": "app.py", "line": 1, "reason": "fixture review finding", "evidence": "fixture reproduction"}]}
        p = self.write("report.json", report)
        self.cmd("respond", "--config", str(self.config_file), "--request", str(self.reqfile), "--report", p, "--enable")
        out = self.root / "important-response.json"
        self.cmd("poll", "--config", str(self.config_file), "--request", str(self.reqfile), "--output", str(out), "--enable")
        self.cmd("import", "--run-dir", str(self.run), "--request", str(self.reqfile), "--response", str(out), "--enable")
        self.flow_cmd("close", ok=False)

if __name__ == "__main__":
    unittest.main(verbosity=2)
