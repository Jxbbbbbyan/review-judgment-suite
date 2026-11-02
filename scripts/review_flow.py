#!/usr/bin/env python3
"""Local evidence/state coordinator. No LLM, network, sandbox or identity provider."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

DIMENSIONS = {"correctness", "security", "end-to-end", "conventions"}
ORDER = ["judgment", "verification", "risk", "review", "adjudication"]

class GateError(Exception):
    pass

def require(ok, message):
    if not ok:
        raise GateError(message)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def text(value):
    return isinstance(value, str) and bool(value.strip())

def snapshot(s):
    root = Path(s["project"])
    files = {}
    for name in s["scope"]:
        p = (root / name).resolve()
        require(p.is_relative_to(root), "scope escapes project (including symlinks)")
        require(not p.exists() or p.is_file(), "scope entries must be files")
        files[name] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    for name in s.get("owners", []):
        p = Path(name)
        files["@owner:" + name] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    return files

def invalidate(s, target):
    index = ORDER.index(target)
    if index <= 0:
        s["judgments"] = {}
    if index <= 1:
        s["checks"] = []
    if index <= 2:
        s["risk"] = None
    if index <= 3:
        s["reports"] = []
    s["decisions"] = {}
    for issue in s.get("issues", {}).values():
        issue["resolution"] = None
    s["approvals"] = []
    s["judgments"].pop("close", None)
    if index <= 3:
        s["judgments"].pop("review", None)
    s["closed"] = False

def event(s, action, detail):
    s["events"].append({"sequence": len(s["events"]) + 1, "at": time.time(),
                        "action": action, "detail": detail, "snapshot": s["snapshot"]})

def refresh(s):
    current = snapshot(s)
    if current != s["files"]:
        require(s["round"] < s["max_rounds"], "content changed after rework budget exhausted; redesign required")
        s["round"] += 1
        s["files"] = current
        s["snapshot"] = digest(current)
        invalidate(s, "judgment")
        s["failure_pending"] = False
        s["parameter_retries"] = 0
        event(s, "content-changed", "all gates invalidated; fresh checks and review required")

def verification_ready(s):
    return bool(s["checks"]) and all(c["exit_code"] == 0 and not c["timeout"] for c in s["checks"])

def reopen_review(s):
    if s["reports"]:
        require(s["round"] < s["max_rounds"], "review round budget exhausted; redesign or handoff required")
        s["round"] += 1

def reviews_ready(s):
    covered = set()
    for r in s["reports"]:
        covered.update(r["dimensions"])
    return covered == DIMENSIONS and bool(s["reports"])

def scope_ready(s):
    require(s["judgments"].get("scope", {}).get("decision") == "proceed", "scope judgment required")

def risk_ready(s):
    scope_ready(s)
    require(verification_ready(s), "successful executable verification required")
    require(s["risk"] is not None, "risk assessment required")

def review_ready(s):
    risk_ready(s)
    if s["mode"] == "joint":
        require("review" in s["judgments"], "joint mode requires a review checkpoint judgment")

def findings(s):
    return [f for r in s["reports"] for f in r["findings"]]

def atomic_save(file, s):
    fd, name = tempfile.mkstemp(prefix=".state-", dir=file.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
            json.dump(s, out, ensure_ascii=False, indent=2)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, file)
    finally:
        if os.path.exists(name):
            os.unlink(name)

@contextlib.contextmanager
def locked(directory):
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / ".lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise GateError("run locked; do not retry blindly; inspect live owner before manual lock recovery")
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield directory / "state.json"
    finally:
        lock.unlink()

def init(args, file):
    require(not file.exists(), "run already exists; use another run directory")
    project = Path(args.project).resolve()
    require(project.is_dir(), "project directory missing")
    require(text(args.task), "task must be nonempty")
    require(1 <= args.max_rounds <= 3, "max-rounds must be 1..3")
    require(1 <= args.route_budget <= 50, "route-budget must be 1..50")
    scope = []
    for value in args.scope:
        p = Path(value)
        require(not p.is_absolute() and ".." not in p.parts and value != ".", "scope must be project-relative files")
        scope.append(p.as_posix())
    require(len(scope) == len(set(scope)) and bool(scope), "scope must be unique and nonempty")
    s = {"schema": 1, "task": args.task, "project": str(project), "scope": scope,
         "mode": args.mode, "round": 1, "max_rounds": args.max_rounds,
         "route_budget": args.route_budget, "judgments": {}, "checks": [], "risk": None,
         "reports": [], "decisions": {}, "approvals": [], "events": [], "closed": False,
         "terminal": None, "issues": {}, "failure_pending": False,
         "parameter_retries": 0, "last_failed_argv": None, "failure_class": None,
         "owners": sorted(set(str(Path(x).resolve()) for x in args.owner)), "finding_ids": []}
    for name in ("AGENTS.md", "CLAUDE.md", "REVIEW.md"):
        for directory in (project, *project.parents):
            p = directory / name
            if p.is_file() and str(p) not in s["owners"]:
                s["owners"].append(str(p))
    require(all(Path(x).is_file() for x in s["owners"]), "declared owner document missing")
    s["files"] = snapshot(s)
    s["snapshot"] = digest(s["files"])
    event(s, "init", {"mode": args.mode, "scope": scope})
    return s

def operate(args, s, run):
    action = args.action
    if action in {"status", "report"}:
        return
    require(not s["closed"] and not s["terminal"], "run is closed/stopped; start a new explicitly authorised run")
    if action == "judge":
        require(text(args.reason), "judgment reason required")
        if args.checkpoint != "scope":
            risk_ready(s)
        if args.checkpoint == "close":
            require(reviews_ready(s), "independent review coverage required before close checkpoint")
        owners = []
        for owner in args.owner:
            p = Path(owner).resolve()
            require(p.is_file(), "invoked owner document unavailable: handoff instead of inventing its rules")
            require(str(p) in s["owners"], "owner must be declared at init so changes invalidate evidence")
            owners.append({"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
        if s["failure_pending"]:
            require(args.failure_class != "none", "failure attribution required")
            if args.failure_class in {"denied", "unknown"}:
                require(args.decision != "proceed", "denial/unknown cannot authorise retry or fallback")
            if args.failure_class == "domain" and args.decision == "proceed":
                require(bool(owners), "domain disposition requires an invoked owner; otherwise handoff")
            if args.failure_class == "parameters" and args.decision == "proceed":
                require(s["parameter_retries"] < 1, "parameter retry already used; handoff or fresh content required")
                s["parameter_retries"] += 1
            s["failure_class"] = args.failure_class
            s["failure_pending"] = False
        s["judgments"][args.checkpoint] = {"decision": args.decision, "reason": args.reason,
                                           "execution": args.execution, "owners": owners,
                                           "failure_class": args.failure_class}
        if args.decision != "proceed":
            s["terminal"] = args.decision
        event(s, action, s["judgments"][args.checkpoint])
    elif action == "check":
        scope_ready(s)
        argv = json.loads(args.argv_json)
        require(isinstance(argv, list) and argv and all(text(x) for x in argv), "argv-json must be a nonempty string array")
        if s["failure_class"] in {"parameters", "tool"}:
            require(argv != s["last_failed_argv"], "corrected input or alternative tool must differ from failed argv")
        require(0 < args.timeout <= 3600, "timeout must be 1..3600 seconds")
        if s["reports"]:
            require(s["round"] < s["max_rounds"], "review round budget exhausted; redesign or handoff required")
        start = time.time()
        # Direct execution only. This is not a sandbox: the caller authorises this command.
        log = run / ("check-%d-%d.log" % (s["round"], len(s["events"]) + 1))
        timed_out = False
        with log.open("wb") as output:
            try:
                result = subprocess.run(argv, cwd=s["project"], stdout=output,
                                        stderr=subprocess.STDOUT, timeout=args.timeout, shell=False)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code, timed_out = 124, True
            except OSError as exc:
                output.write(str(exc).encode("utf-8"))
                code = 127
        record = {"argv": argv, "exit_code": code, "timeout": timed_out,
                  "elapsed": round(time.time() - start, 4), "log": log.name,
                  "sha256": hashlib.sha256(log.read_bytes()).hexdigest()}
        if snapshot(s) != s["files"]:
            refresh(s)
            event(s, "check-invalidated", record)
            raise GateError("check changed scoped content; evidence discarded, judge/check again")
        # New execution invalidates downstream decisions even if its command succeeds.
        reopen_review(s)
        invalidate(s, "risk")
        s["checks"].append(record)
        event(s, action, record)
        if code != 0:
            s["judgments"] = {}
            s["failure_pending"] = True
            s["last_failed_argv"] = argv
            raise GateError("check failed; attribute failure and rejudge before further work")
    elif action == "risk":
        scope_ready(s)
        require(verification_ready(s), "successful checks required; clear failed verification via route after attribution")
        require(text(args.reason), "risk reason required")
        reopen_review(s)
        invalidate(s, "risk")
        required = {"low": 0, "medium": 1, "high": 2}[args.level]
        s["risk"] = {"level": args.level, "sensitive": args.sensitive,
                     "reason": args.reason, "human_approvals": max(required, int(args.sensitive))}
        event(s, action, s["risk"])
    elif action == "review":
        review_ready(s)
        r = read_json(args.input)
        require(isinstance(r, dict), "review must be an object")
        require(r.get("snapshot") == s["snapshot"], "stale review snapshot")
        require(text(r.get("reviewer")) and r.get("independent") is True, "independent reviewer declaration required")
        require(r["reviewer"] not in {x["reviewer"] for x in s["reports"]}, "reviewer already submitted")
        dims = r.get("dimensions")
        require(isinstance(dims, list) and bool(dims) and set(dims) <= DIMENSIONS, "invalid review dimensions")
        require(isinstance(r.get("findings"), list), "findings must be an array")
        ids = set(s["finding_ids"])
        for f in r["findings"]:
            require(isinstance(f, dict), "finding must be an object")
            require(text(f.get("id")) and f["id"] not in ids, "unique finding id required")
            ids.add(f["id"])
            require(f.get("tag") in {"Important", "Nit", "Pre-existing"}, "invalid finding tag")
            require(f.get("file") in s["scope"], "finding file must be in scope; expand via a new run")
            require(type(f.get("line")) is int and f["line"] >= 1, "positive line number required")
            p = Path(s["project"]) / f["file"]
            require(p.exists() and f["line"] <= len(p.read_text(encoding="utf-8").splitlines()), "finding line outside file")
            require(text(f.get("evidence")) and text(f.get("reason")), "finding evidence and reason required")
        fixed = r.get("verified_fixed", [])
        require(isinstance(fixed, list), "verified_fixed must be an array")
        for value in fixed:
            require(isinstance(value, dict) and value.get("id") in s["issues"], "unknown issue in verified_fixed")
            require(text(value.get("evidence")), "independent fix verification evidence required")
            require(s["issues"][value["id"]]["snapshot"] != s["snapshot"], "fixed requires changed content")
        s["reports"].append(r)
        s["finding_ids"].extend(f["id"] for f in r["findings"])
        for issue in s["issues"].values():
            issue["resolution"] = None
        for f in r["findings"]:
            if f["tag"] == "Important":
                s["issues"][f["id"]] = {"finding": f, "snapshot": s["snapshot"], "resolution": None}
        s["decisions"] = {}
        s["approvals"] = []
        s["judgments"].pop("close", None)
        event(s, action, {"reviewer": r["reviewer"], "dimensions": dims})
    elif action == "adjudicate":
        review_ready(s)
        require(reviews_ready(s), "all four independent review dimensions required")
        decisions = read_json(args.input)
        require(isinstance(decisions, dict), "decisions must be an object keyed by finding id")
        known = {f["id"] for f in findings(s)} | set(s["issues"])
        require(set(decisions) <= known, "unknown finding in decisions")
        for key, d in decisions.items():
            require(isinstance(d, dict) and d.get("action") in {"reject", "defer", "fixed"}, "invalid disposition")
            require(text(d.get("reason")) and text(d.get("evidence")), "disposition reason and evidence required")
            if d["action"] == "fixed":
                confirmations = [v for r in s["reports"] for v in r.get("verified_fixed", [])]
                require(any(v["id"] == key for v in confirmations), "fixed requires current independent verification")
        s["decisions"] = decisions
        for issue in s["issues"].values():
            issue["resolution"] = None
        for key, value in decisions.items():
            if key in s["issues"]:
                s["issues"][key]["resolution"] = dict(value, resolved_snapshot=s["snapshot"])
        s["approvals"] = []
        s["judgments"].pop("close", None)
        event(s, action, decisions)
    elif action == "approve":
        review_ready(s)
        require(reviews_ready(s), "review required before approval")
        a = read_json(args.input)
        require(isinstance(a, dict) and a.get("kind") == "human" and text(a.get("actor")), "human approval attestation required")
        require(a.get("snapshot") == s["snapshot"] and text(a.get("evidence")), "approval snapshot and evidence required")
        require(a["actor"] not in {v["actor"] for v in s["approvals"]}, "distinct human actors required")
        s["approvals"].append(a)
        event(s, action, a)
    elif action == "route":
        require(text(args.reason) and s["route_budget"] > 0, "routing requires reason and remaining budget")
        if s["mode"] == "serial":
            require(args.target == "judgment", "serial mode restarts at judgment; choose adaptive for stage jumps")
        if args.target == "risk":
            scope_ready(s)
            require(verification_ready(s), "cannot jump over verification")
        if args.target in {"review", "adjudication"}:
            risk_ready(s)
        if args.target == "adjudication":
            require(reviews_ready(s), "cannot jump over review")
        if args.target != "adjudication":
            reopen_review(s)
        s["route_budget"] -= 1
        invalidate(s, args.target)
        # Every adaptive/backward route reopens scope judgment: retain boundary control.
        s["judgments"] = {}
        event(s, action, {"target": args.target, "reason": args.reason})
    elif action == "close":
        review_ready(s)
        require(reviews_ready(s), "four-dimensional independent review required")
        if s["mode"] == "joint":
            require("close" in s["judgments"], "joint mode requires a close checkpoint judgment")
        for issue in s["issues"].values():
            resolution = issue["resolution"] or {}
            require(resolution.get("action") in {"fixed", "reject"} and resolution.get("resolved_snapshot") == s["snapshot"],
                    "unresolved Important; fix and independently verify, or justify rejection on current snapshot")
        require(len(s["approvals"]) >= s["risk"]["human_approvals"], "required human approval attestations missing")
        for c in s["checks"]:
            p = run / c["log"]
            require(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == c["sha256"], "check log changed or missing")
        s["closed"] = True
        event(s, action, "complete within declared scope; no publish performed")

def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir", required=True)
    sub = p.add_subparsers(dest="action", required=True)
    q = sub.add_parser("init")
    q.add_argument("--project", required=True); q.add_argument("--task", required=True)
    q.add_argument("--scope", nargs="+", required=True)
    q.add_argument("--mode", choices=["serial", "joint", "adaptive"], default="adaptive")
    q.add_argument("--max-rounds", type=int, default=3); q.add_argument("--route-budget", type=int, default=12)
    q.add_argument("--owner", action="append", default=[])
    q = sub.add_parser("judge")
    q.add_argument("--checkpoint", choices=["scope", "review", "close"], default="scope")
    q.add_argument("--decision", choices=["proceed", "stop", "handoff"], required=True)
    q.add_argument("--execution", choices=["deterministic", "agent"], required=True)
    q.add_argument("--reason", required=True); q.add_argument("--owner", action="append", default=[])
    q.add_argument("--failure-class", choices=["none", "tool", "parameters", "environment", "domain", "denied", "unknown"], default="none")
    q = sub.add_parser("check")
    q.add_argument("--argv-json", required=True); q.add_argument("--timeout", type=int, default=120)
    q = sub.add_parser("risk")
    q.add_argument("--level", choices=["low", "medium", "high"], required=True)
    q.add_argument("--reason", required=True); q.add_argument("--sensitive", action="store_true")
    for name in ["review", "adjudicate", "approve"]:
        sub.add_parser(name).add_argument("--input", required=True)
    q = sub.add_parser("route")
    q.add_argument("--target", choices=ORDER, required=True); q.add_argument("--reason", required=True)
    for name in ["status", "report", "close"]:
        sub.add_parser(name)
    return p

def main(argv=None):
    args = parser().parse_args(argv)
    try:
        run = Path(args.run_dir).resolve()
        with locked(run) as file:
            s = None
            try:
                if args.action == "init":
                    s = init(args, file)
                else:
                    require(file.is_file(), "run not initialised")
                    s = read_json(file)
                    require(s.get("schema") == 1, "unsupported state schema")
                    if s["closed"] or s["terminal"]:
                        require(args.action in {"status", "report"}, "run is closed/stopped; start a new explicitly authorised run")
                    else:
                        refresh(s)
                    operate(args, s, run)
            finally:
                if s is not None:
                    atomic_save(file, s)
            print(json.dumps(s, ensure_ascii=False, indent=2))
        return 0
    except (GateError, ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
