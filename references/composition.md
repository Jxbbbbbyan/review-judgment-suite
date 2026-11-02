# Judgment and review workflow contract / 判断与审核流程契约

Judgment decides the permitted direction and next action. Review supplies verified findings and executable evidence. Their handoff is a feedback loop: scope and decision criteria go into review; findings and coverage limits return to judgment. The runner records and checks the required evidence; it cannot make either kind of substantive decision. [Authorship and review reference](sources.md).

Judgment 确定行动方向、边界和下一步；Review 提供检查输出、经过复核的问题及覆盖边界。两者通过证据形成反馈关系。脚本检查记录和前置条件，不替使用者决定方向，也不证明一个没有查出问题的结果一定正确。

## Who owns which decision / 谁决定什么

| Concern / 事项 | Judgment contribution / 判断层 | Layered-review contribution / 审查层 | Runner / 脚本 |
|---|---|---|---|
| Scope and cost / 范围成本 | Decide whether to act; bounded options and communication cost | Preserve task intent and conventions | Declared file scope, round and route budgets |
| Evidence / 证据 | Distinguish unknown outcomes, bad inputs and domain results | Execute checks; recheck candidate findings | Executes explicit argv; hashes logs and scoped content |
| Review / 复核 | Decide when more work changes the outcome | Four perspectives; risk; dispositions | Validate declared coverage and required fields |
| Completion / 结束 | Stop with evidence rather than expand indefinitely | Important convergence; approvals; limits | Reject incomplete or stale close attempts |

The script checks **process evidence**, not truth. It cannot tell whether a check is sufficient, a reviewer was really isolated, a finding was honestly tagged, a risk label was accurate, or a human identity was genuine. It also cannot prevent somebody editing its state file or running unrelated commands outside it. Those remain agent/host/reviewer responsibilities.

The [optional cross-model layer](cross-model-review.md) can carry reports from another host/model to these same gates. It is not imported by the core and does not supply a model backend or reviewer independence.

脚本固定可验证的过程条件，不替代工程判断。有人执行 `print('ok')` 并不能因此证明代码正确；JSON 写了 independent 也不等于真正独立。运行目录由调用者控制，不是防篡改审计系统。

## Modes / 三种运行方式

**Serial / 串行:** scope judgment → execution check → risk → independent review → adjudication if needed → close. A manual route always restarts at judgment. Good for a stable change with known boundaries.

**Joint / 联合:** same order, with required judgment checkpoints immediately before review and before close. Judgment reconsiders scope, sufficiency and remaining work; review supplies the factual findings. Workers may review different dimensions in parallel, but that parallelism is supplied by the host, not this CLI.

**Adaptive / 跳转:** same mandatory gates, with explicit backward routes. `route --target verification` clears checks and all downstream gates; `risk` retains successful checks but clears risk/review; `review` retains checks/risk but clears review; `adjudication` retains review but clears dispositions/approvals. Every route clears scope judgment and consumes one routing token. Re-enter judgment, then continue at the selected stage. No jump can manufacture missing prerequisites.

三个模式都不能从“写完”直接跳到“完成”。joint 指判断与审查在关键门交换结论，不意味着自动启动多智能体。adaptive 允许局部回退；一旦内容变化，局部通过状态全部失效，不能只补写一个成功字段。

## Failures and stopping / 失败与停止

After a failed check, a new `judge` must record `--failure-class`: `tool`, `parameters`, `environment`, `domain`, `denied`, or `unknown`. This classification is a human/agent interpretation, not error-text detection. A denial or unknown outcome cannot proceed. A domain continuation needs a readable, declared owner. Tool replacement or parameter correction must change argv; parameter correction is allowed once per snapshot. Route to verification to discard failed checks, then re-enter scope judgment.

环境未就绪不应被冒充工具损坏；排队、OOM、数值不收敛不适用盲目重试。拒绝事件不能被写成工具故障来绕过。脚本不会自动判断这些语义，调用者必须说明证据；若无法区分，handoff。

Stop/handoff reports contain: last successful checkpoint; excluded hypotheses with evidence; current error/output; two or three feasible options with costs; a counterexample check explaining why stopping is appropriate. No script-imposed “ask again” is needed for choices already authorised by the user.

## External owners / 外部规则

You can run this workflow without the author's original presets. Generic review does not require the original context-handoff, planning or compute-resource skills. If an active branch relies on one, supply its actual document at `init --owner` and invoke it with `judge --owner`; its hash participates in the snapshot. Missing document → handoff that branch; do not invent its GPU thresholds, context percentages or approval rules. An unrelated missing document is not a global blocker.

适用的上级规则优先。判断确定性执行时，本流程要求步骤、输入和失败分支三项均已知；原 judgment 快照中“任一确定就编排”与“三项全确定才编排”两种表述的适配差异在此记录，快照本身不改。

## Budgets, integrity and limits / 预算与边界

At most 3 review/content rounds, including the initial pass; default 12 route tokens. Reopening verification, risk or review after reports already exist also advances the round, even if source content is unchanged. The review article calls for stepping back after three review rounds; this runner counts content changes and reopened passes as well. The route budget is a project implementation choice, not a published quality threshold. Adjust it at init, never silently extend a live run. Exhaustion is not success.

Only declared files and applicable convention/owner files are hashed. Added and deleted declared paths change the snapshot; a rename must declare both names. An unrelated file outside declared scope is not inspected automatically. Updating scope requires a new run. Checks may create ignored caches outside scope; the runner does not clean them.

Each command takes an exclusive lock and atomically replaces state JSON. A crashed process can leave `.lock`; inspect PID/liveness and incomplete checks before manually removing it. Do not delete a live lock. A timed-out check kills the direct process via Python; descendants may need host-level containment and observation. Neither a lock nor SHA-256 protects against a malicious local owner. Keep runtime directories private and outside packages.
