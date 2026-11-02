# CLI and state / 命令与状态

Python 3.10+; standard library only. Run from the package directory. Replace `python` with your real interpreter (for example `python3` on Linux). Runtime output is JSON; errors use stderr and exit 2, success uses exit 0. The child command's actual code is retained in state, including timeout=124 and missing executable=127.

## First pass / 首轮

```powershell
python scripts/review_flow.py --run-dir ../review-run init --project ../target-project --task "Review the parser change" --scope parser.py tests/test_parser.py --mode adaptive
python scripts/review_flow.py --run-dir ../review-run judge --decision proceed --execution agent --reason "Two declared files; the parser contract requires interpretation"
python scripts/review_flow.py --run-dir ../review-run check --argv-json '["python", "-m", "unittest", "discover", "-s", "tests", "-v"]'
python scripts/review_flow.py --run-dir ../review-run risk --level low --reason "Internal parser; no sensitive paths"
python scripts/review_flow.py --run-dir ../review-run status
```

`--project` is the child command's working directory. `--scope` is the **file-level** review contract, not a directory glob. Include both old and new paths for a rename. Paths cannot traverse outside the project, including through symlinks. Root/ancestor AGENTS.md, CLAUDE.md and REVIEW.md are included automatically if present. Additional rules use `init --owner path/to/rule.md`; declare before starting so content changes invalidate decisions.

Owner paths resolve from the caller's current directory, not from `--project`. Use an absolute readable path when calling from elsewhere.

Shell pipelines and redirections are not interpreted by `check`. It executes an argv array with `shell=False`. To use a shell deliberately, provide its executable and arguments explicitly, only within the task's authority. Do not put credentials in command arguments, state, logs or review JSON. Logs stream to files rather than filling the runner's memory.

`check` records what actually ran but cannot judge adequacy. Choose a check that fails when the claimed behaviour is wrong. A failed execution clears judgment and downstream evidence; it is never silently treated as a pass. A command that edits scoped content invalidates its own result and requires a fresh run of verification.

## Independent review input / 独立审查输入

Create the reviewer task in a separate host context. Give it intent, diff/current files, scope and applicable rules. Ask it to verify candidate findings before returning JSON. The imported `snapshot` comes from current `status`; it is a digest, not a timestamp or a branch name.

```json
{
  "snapshot": "COPY_CURRENT_STATUS_SNAPSHOT",
  "reviewer": "independent-reviewer-a",
  "independent": true,
  "dimensions": ["correctness", "security", "end-to-end", "conventions"],
  "findings": [
    {
      "id": "A-1",
      "tag": "Important",
      "file": "parser.py",
      "line": 12,
      "reason": "Explain the introduced failure and affected callers",
      "evidence": "Exact reproducer, result and source evidence"
    }
  ],
  "verified_fixed": []
}
```

Use `findings: []` for a clean review; do not invent an issue to fill the template. A worker may cover a subset of dimensions; the union must cover all four before completion. Reviewer IDs must be unique within the current pass; finding IDs are unique across the entire run, including prior Nits and pre-existing findings. Use verified_fixed to refer to an old issue, not a new finding with its ID. Findings must cite current in-scope files and real positive line numbers; deleted-file findings should cite an existing changed caller or test, or remain a narrative limitation. The script does not semantically validate evidence or authenticate reviewer independence.

```powershell
python scripts/review_flow.py --run-dir ../review-run review --input ../review.json
python scripts/review_flow.py --run-dir ../review-run close
```

For `joint`, insert `judge --checkpoint review ...` after risk and before importing reports, and `judge --checkpoint close ...` before closing. The remaining judgment arguments are the same as the initial scope judgment.

## Findings, repairs and re-entry / 问题、修复与重入

An Important persists in `issues`, even if reports are cleared or a later worker submits no findings. Merely marking it `fixed` is rejected. After a code fix, the next command detects the snapshot change: round increments, judgment/checks/risk/reviews/approvals invalidate. Re-enter judgment, execute checks, assess risk and obtain a fresh independent review. That reviewer can include:

```json
{"verified_fixed": [{"id": "A-1", "evidence": "The old reproducer fails on the original content and passes after the fix; same-class callers checked"}]}
```

This field belongs in a full current review object, not a standalone report. Then import decisions:

```json
{
  "A-1": {
    "action": "fixed",
    "reason": "Boundary handling repaired across the affected call sites",
    "evidence": "Current independent confirmation plus check log reference"
  }
}
```

```powershell
python scripts/review_flow.py --run-dir ../review-run adjudicate --input ../decisions.json
python scripts/review_flow.py --run-dir ../review-run close
```

`reject` is for a rechecked false positive or intentional behaviour with evidence; it is not a generic waiver. `defer` may document a Nit or pre-existing issue, but does not resolve an Important. Every disposition needs reason and evidence. Prior resolutions become stale when content changes; reconfirm or re-adjudicate them on the current snapshot.

## Stage jumps / 跨步骤切换

```powershell
python scripts/review_flow.py --run-dir ../review-run route --target review --reason "Need a second independent view of the same content"
python scripts/review_flow.py --run-dir ../review-run judge --decision proceed --execution agent --reason "Scope unchanged; evidence still applicable"
```

Route targets are `judgment`, `verification`, `risk`, `review`, `adjudication`. There is no route-to-complete. Forward targets check upstream evidence before changing state. All routes clear scope judgment; read [composition](composition.md) for what each target invalidates. `serial` permits only a return to judgment. At round 3, any further content change or reopening of an existing review pass is refused for this run: redesign or hand off, preserving the prior ledger.

After a parameter-related check failure:

```powershell
python scripts/review_flow.py --run-dir ../review-run judge --decision proceed --execution deterministic --failure-class parameters --reason "The test module path was misspelled; correct that specific argument"
python scripts/review_flow.py --run-dir ../review-run route --target verification --reason "Discard the failed check, keep its event history"
python scripts/review_flow.py --run-dir ../review-run judge --decision proceed --execution deterministic --reason "Corrected command is within original scope"
```

Then execute the changed argv. Classification is retained across invocations. A second parameter-correction permission is blocked for the same snapshot. For `denied` or `unknown`, choose stop/handoff instead; do not change tools to bypass the restriction. For domain continuation, supply an owner previously declared at init. Record last success, eliminated explanations, evidence, options and counterexample check in the judgment reason or an accompanying report.

## Human decisions / 人工决定

At least one human for Medium or sensitive paths; two for High. `--sensitive` can require human judgment for any additional case. Supply an attestation only when that actual approval exists:

```json
{"snapshot":"COPY_CURRENT_STATUS_SNAPSHOT","kind":"human","actor":"reviewer-identifier","evidence":"Reference to the actual approval record and its scope"}
```

```powershell
python scripts/review_flow.py --run-dir ../review-run approve --input ../approval.json
```

Approval records are attestations, not cryptographic identity proof. Reusing an actor does not count twice. Never set `kind: human` for an AI response. Do not export private approval records. This suite does not broaden permission granted by the user or host.

## State and recovery / 状态与恢复

`state.json` holds task/scope, snapshot hashes, current gates, persistent Important obligations, check records, judgments, approvals and ordered events. `check-*.log` holds actual merged stdout/stderr. `status` and `report` both emit the current JSON ledger; a coordinator supplies the readable bilingual explanation. Neither produces an independent semantic verdict by itself.

Do not share raw run folders: task descriptions, project paths, command arguments and output can be private. Keep them outside the distributable tree. Preserve raw evidence locally; publish curated summaries with private identifiers removed. The package's `examples/` contains such summaries, never the original run directory.
