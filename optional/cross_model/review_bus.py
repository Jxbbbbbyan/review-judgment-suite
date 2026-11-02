#!/usr/bin/env python3
"""Opt-in file gateway for review messages. No model SDK or listening service."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid

LIMIT = 1024 * 1024
FIELDS = {"schema", "request_id", "snapshot", "run_binding", "scope", "source", "target", "context", "digest"}
DIMENSIONS = {"correctness", "security", "end-to-end", "conventions"}

class BusError(Exception):
    pass

def need(value, message):
    if not value:
        raise BusError(message)

def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, "duplicate JSON key")
        result[key] = value
    return result

def load(file):
    p = Path(file)
    need(p.is_file() and p.stat().st_size <= LIMIT, "missing or oversized JSON file")
    result = json.loads(p.read_text(encoding="utf-8-sig"), object_pairs_hook=strict_pairs)
    need(isinstance(result, dict), "JSON object required")
    return result

def encoded(value):
    data = (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()
    need(len(data) <= LIMIT, "message exceeds 1 MiB")
    return data

def checksum(value):
    return hashlib.sha256(encoded(value)).hexdigest()

def identifier(value):
    need(isinstance(value, str), "request id must be text")
    need(str(uuid.UUID(value)) == value, "canonical UUID request id required")
    return value

def label(value):
    need(isinstance(value, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", value), "invalid host label")
    return value

def model(value):
    need(isinstance(value, str) and 0 < len(value) <= 120 and value == value.strip() and value.isprintable(), "canonical model label required")
    return value

def safe(root, *parts):
    p = root.joinpath(*parts).resolve()
    need(p.is_relative_to(root), "mailbox path escapes configured root")
    return p

@contextlib.contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise BusError("message locked; inspect the live owner before manual recovery")
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        path.unlink()

def publish(file, value):
    p = Path(file).resolve()
    data = encoded(value)
    with lock(p.with_name(p.name + ".lock")):
        need(not p.exists(), "destination already exists; no duplicate delivery or overwrite")
        fd, temp = tempfile.mkstemp(prefix=".message-", dir=p.parent)
        try:
            with os.fdopen(fd, "wb") as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, p)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

def validate_request(r):
    need(set(r) == FIELDS and r.get("schema") == 1, "unexpected request schema or executable fields")
    identifier(r["request_id"])
    need(isinstance(r["snapshot"], str) and re.fullmatch(r"[0-9a-f]{64}", r["snapshot"]), "invalid snapshot")
    need(isinstance(r["run_binding"], str) and re.fullmatch(r"[0-9a-f]{64}", r["run_binding"]), "invalid run binding")
    need(isinstance(r["scope"], list) and bool(r["scope"]), "scope list required")
    for f in r["scope"]:
        need(isinstance(f, str) and not Path(f).is_absolute() and ".." not in Path(f).parts, "invalid scope file")
    for side in ("source", "target"):
        need(isinstance(r[side], dict) and set(r[side]) == {"host", "model"}, "host/model pair required")
        label(r[side]["host"]); model(r[side]["model"])
    need(r["source"]["model"].casefold() != r["target"]["model"].casefold(), "cross-model route requires different declared models")
    need(isinstance(r["context"], dict) and set(r["context"]) == {"intent", "diff", "conventions"}, "explicit intent/diff/conventions context required")
    need(all(isinstance(v, str) for v in r["context"].values()) and r["context"]["intent"].strip(), "invalid context")
    need(r["digest"] == checksum({k: v for k, v in r.items() if k != "digest"}), "request digest mismatch")
    return r

def config(file, enabled):
    c = load(file)
    need(enabled and c.get("enabled") is True, "cross-model routing disabled; opt in through config and --enable")
    need(c.get("schema") == 1 and isinstance(c.get("spool_root"), str) and c["spool_root"].strip(), "invalid route config")
    p = Path(c["spool_root"])
    root = (p if p.is_absolute() else Path(file).resolve().parent / p).resolve()
    need(isinstance(c.get("routes"), list), "configured routes required")
    for row in c["routes"]:
        need(isinstance(row, dict) and set(row) == {"source", "target"}, "invalid route")
        label(row["source"]); label(row["target"])
    return c, root

def allowed(c, r):
    need({"source": r["source"]["host"], "target": r["target"]["host"]} in c["routes"], "route not configured")

def validate_report(r, report):
    need(isinstance(report, dict) and report.get("snapshot") == r["snapshot"], "stale or malformed review report")
    need(report.get("independent") is True and isinstance(report.get("reviewer"), str) and report["reviewer"].strip(), "independent reviewer declaration required")
    dims = report.get("dimensions")
    need(isinstance(dims, list) and bool(dims) and all(isinstance(x, str) for x in dims) and set(dims) <= DIMENSIONS, "invalid review dimensions")
    need(isinstance(report.get("findings"), list), "review findings array required")
    encoded(report)

def response(r, report):
    validate_report(r, report)
    return {"schema": 1, "request_id": r["request_id"], "request_digest": r["digest"],
            "snapshot": r["snapshot"], "reviewer_host": r["target"], "report": report}

def validate_response(r, value):
    need(set(value) == {"schema", "request_id", "request_digest", "snapshot", "reviewer_host", "report"}, "invalid response schema")
    need(value["schema"] == 1 and value["request_id"] == r["request_id"] and value["request_digest"] == r["digest"], "response does not belong to this request")
    need(value["snapshot"] == r["snapshot"] and value["reviewer_host"] == r["target"], "response target or snapshot mismatch")
    validate_report(r, value["report"])
    return value

def core():
    p = Path(__file__).resolve().parents[2] / "scripts" / "review_flow.py"
    spec = importlib.util.spec_from_file_location("review_flow_optional_import", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def run_binding(state):
    return checksum({"project": state["project"], "task": state["task"],
                     "initial_event": state["events"][0], "scope": state["scope"]})

def create(args):
    flow = core()
    state = flow.read_json(Path(args.run_dir) / "state.json")
    need(not state["closed"] and not state["terminal"], "cannot request review for a closed run")
    flow.review_ready(state)
    need(flow.snapshot(state) == state["files"], "content changed; refresh and re-verify the core run first")
    ctx = load(args.context)
    need(set(ctx) == {"intent", "diff", "conventions"}, "context must contain only explicitly selected review material")
    r = {"schema": 1, "request_id": str(uuid.uuid4()), "snapshot": state["snapshot"], "run_binding": run_binding(state),
         "scope": state["scope"], "source": {"host": args.source_host, "model": args.source_model},
         "target": {"host": args.target_host, "model": args.target_model}, "context": ctx}
    r["digest"] = checksum(r)
    validate_request(r)
    publish(args.output, r)
    return {"request_id": r["request_id"], "snapshot": r["snapshot"], "prepared_only": True}

def transport(args):
    c, root = config(args.config, args.enable)
    action = args.action
    if action == "send":
        r = validate_request(load(args.request))
        allowed(c, r)
        need(args.confirm_share, "inspect selected context and pass --confirm-share before delivery")
        dest = safe(root, "requests", r["target"]["host"], r["request_id"] + ".json")
        publish(dest, r)
        return {"request_id": r["request_id"], "queued": True, "completed": False}
    if action in {"gateway", "take", "work"}:
        target, rid = label(args.target), identifier(args.request_id)
        folder = "requests" if action == "gateway" else "inbox"
        r = validate_request(load(safe(root, folder, target, rid + ".json")))
        need(r["target"]["host"] == target and r["request_id"] == rid, "mailbox envelope mismatch")
        allowed(c, r)
        if action == "gateway":
            publish(safe(root, "inbox", target, rid + ".json"), r)
            return {"request_id": rid, "forwarded": True, "completed": False}
        if action == "take":
            publish(args.output, r)
            return {"request_id": rid, "received": True, "completed": False}
        workers = c.get("workers", {})
        need(isinstance(workers, dict) and isinstance(workers.get(target), dict), "no configured worker for this target")
        w = workers[target]
        need(w.get("model") == r["target"]["model"], "worker model label differs from requested target")
        argv = w.get("argv")
        need(isinstance(argv, list) and bool(argv) and all(isinstance(x, str) and x for x in argv), "worker argv must be a nonempty string array")
        need(isinstance(w.get("cwd"), str), "explicit worker cwd required")
        cwd = Path(w["cwd"])
        cwd = (cwd if cwd.is_absolute() else Path(args.config).resolve().parent / cwd).resolve()
        need(cwd.is_dir(), "worker cwd missing")
        need(1 <= args.timeout <= 3600, "worker timeout must be 1..3600 seconds")
        started = safe(root, "work", target, rid + ".started.json")
        need(not safe(root, "responses", r["source"]["host"], rid + ".json").exists(), "response already returned; do not rerun worker")
        # Deliberately permanent: a crash/timeout may have consumed a remote request.
        publish(started, {"request_id": rid, "at": time.time(), "status": "started-no-automatic-retry"})
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            result = subprocess.run(argv, input=encoded(r), stdout=output, stderr=errors,
                                    cwd=cwd, timeout=args.timeout, shell=False)
            need(result.returncode == 0, "worker failed; started receipt retained, inspect before manual recovery")
            need(output.tell() <= LIMIT, "worker response exceeds size limit")
            output.seek(0)
            report = json.loads(output.read().decode("utf-8"), object_pairs_hook=strict_pairs)
        value = response(r, report)
        publish(safe(root, "responses", r["source"]["host"], rid + ".json"), value)
        return {"request_id": rid, "report_returned": True, "imported": False}
    r = validate_request(load(args.request))
    allowed(c, r)
    if action == "respond":
        value = response(r, load(args.report))
        # Require evidence of gateway delivery before accepting a return.
        delivered = validate_request(load(safe(root, "inbox", r["target"]["host"], r["request_id"] + ".json")))
        need(delivered == r, "request differs from delivered copy")
        publish(safe(root, "responses", r["source"]["host"], r["request_id"] + ".json"), value)
        return {"request_id": r["request_id"], "report_returned": True, "imported": False}
    value = validate_response(r, load(safe(root, "responses", r["source"]["host"], r["request_id"] + ".json")))
    publish(args.output, value)
    return {"request_id": r["request_id"], "response_received": True, "imported": False}

def import_report(args):
    need(args.enable, "cross-model import requires --enable")
    r = validate_request(load(args.request))
    value = validate_response(r, load(args.response))
    flow = core()
    state = flow.read_json(Path(args.run_dir) / "state.json")
    need(run_binding(state) == r["run_binding"], "response belongs to another review run")
    need(state["snapshot"] == r["snapshot"] and state["scope"] == r["scope"], "request is for a different run scope or snapshot")
    need(flow.snapshot(state) == state["files"], "content changed while external review was in flight")
    report = dict(value["report"])
    report["reviewer"] = r["target"]["host"] + "/" + r["target"]["model"] + ":" + report["reviewer"]
    # Preserve every core gate. This does not close the run or approve findings.
    with tempfile.TemporaryDirectory(prefix="review-import-") as d:
        p = Path(d) / "report.json"
        p.write_bytes(encoded(report))
        code = flow.main(["--run-dir", args.run_dir, "review", "--input", str(p)])
    need(code == 0, "core rejected review; inspect its gate error")
    return {"request_id": r["request_id"], "imported": True, "closed": False}

def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    q = sub.add_parser("create")
    for flag in ("run-dir", "context", "source-host", "source-model", "target-host", "target-model", "output"):
        q.add_argument("--" + flag, required=True)
    for name in ("send", "gateway", "take", "work", "respond", "poll"):
        q = sub.add_parser(name)
        q.add_argument("--config", required=True); q.add_argument("--enable", action="store_true")
        if name in {"gateway", "take", "work"}:
            q.add_argument("--target", required=True); q.add_argument("--request-id", required=True)
        else:
            q.add_argument("--request", required=True)
        if name == "send": q.add_argument("--confirm-share", action="store_true")
        if name == "respond": q.add_argument("--report", required=True)
        if name in {"take", "poll"}: q.add_argument("--output", required=True)
        if name == "work": q.add_argument("--timeout", type=int, default=120)
    q = sub.add_parser("import")
    for flag in ("request", "response", "run-dir"): q.add_argument("--" + flag, required=True)
    q.add_argument("--enable", action="store_true")
    return p

def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.action == "create": result = create(args)
        elif args.action == "import": result = import_report(args)
        else: result = transport(args)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (BusError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
