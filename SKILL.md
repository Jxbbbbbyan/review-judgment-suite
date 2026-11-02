---
name: review-judgment-suite
description: Combine action-boundary judgment with layered change review using a local evidence state machine. Use for an explicitly requested combined review, multi-step risky changes, failure attribution, or review handoff that needs resumable evidence; not routine single-step edits.
---

# Review + Judgment / 判断与分层审查

Use Judgment to decide whether to act, how far, when to replan and when to stop. Use layered review to establish what was checked, what risks remain and which findings are resolved. The shared coordinator is [scripts/review_flow.py](scripts/review_flow.py), Python 3.10+ standard library only.

先判断边界，再验证改动；遇到新证据可回到判断节点，但不能跳过验证、独立审查和问题处置。默认选 `adaptive`；固定流程选 `serial`；关键门前都要重判时选 `joint`。完整命令和数据格式见 [workflow](references/workflow.md)。

## Essential rules

1. Read task intent, diff, applicable AGENTS.md / CLAUDE.md / REVIEW.md. Declare the files being reviewed, including deletion/new-file paths and relevant owner documents. Steps, inputs **and** failure branches must all be predetermined before classifying execution as deterministic; the originals contain contradictory wording on this point, resolved here conservatively.
2. Preserve user authorisation and host policy. Scope growth needs a new run with an explicit rationale. The coordinator is neither a sandbox nor an approval authority. A check command can have side effects; only run commands authorised for this task.
3. Execute a meaningful check with `check`; store actual output and exit code. Failed checks require classification before retry. Parameter corrections get one attempt per content snapshot; denial is terminal, while domain/resource failures defer to an invoked, readable owner. Unknown outcome or unavailable owner → `handoff` with evidence and options. Do not disguise an unfinished goal as completion.
4. Record risk: Low / Medium / High. Medium needs one real human approval, High two; authentication, billing, CI, release/install/update paths need at least one. Use `--sensitive` for these or any other case needing human judgment. The script can store attestations, not authenticate their authors. User instructions and host approval mechanisms remain authoritative.
5. Supply a fresh reviewer with only intent, diff/current files, relevant conventions and scope. Do not pass the author's preferred conclusion. Cover correctness, security, end-to-end behaviour and conventions. Independent context must be provided by the host; different names in JSON do not create it. If delegation is unavailable, disclose the limitation and do not call a same-context self-check independent.
6. Recheck candidates against source evidence before submitting a finding: exact file/line, why it is real, introduced-vs-pre-existing, impact and same-class coverage. Label Important / Nit / Pre-existing; omit style-only complaints. Important requires a verified fix on a new snapshot or a documented evidence-based rejection. Nit may be deferred; pre-existing issues are listed, not silently repaired beyond scope.
7. On content or owner changes the runner invalidates checks and review, but carries Important obligations forward. At most three review/content rounds; reopening an existing pass also counts, then redesign/handoff. Same-content routes consume a separate routing budget. Third-round review focuses on the new delta **and** carried issues, never silently drops old issues.
8. `close` only records completion within declared scope. It does not publish, merge, submit to a bot or grant approval. No Grok call is bundled. A stop/handoff run stays terminal; new authority or changed conditions require a new run with links to the earlier evidence.

## Reference routing

- [Composition rules and gates](references/composition.md): loading, mode selection, failures, owner resolution, evidence limits.
- [CLI, state and JSON contracts](references/workflow.md): actual execution and stage jumps.
- [Sources and adaptation record](references/sources.md): official readings versus local conventions; snapshot provenance.
- [Original local skills](sources/): inspection-only snapshots. They are not runtime dependencies; use this combined contract where adaptation differs.

## Output

Start with Important / Nit / Pre-existing counts, then state: ready, fix-and-review, or human decision needed; risk and approvals; verified findings and dispositions; actual commands and output; coverage limits and rollback. Attach the run's evidence path. Do not publish private paths, raw prompts or approval identities in shared reports.
