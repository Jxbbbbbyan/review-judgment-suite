<sub><em>特别致敬：<br>
最清白、最懂安全、最尊重版权、最不会蒸馏、最严于律己宽于待人、最不喜欢把模型降智给用户限流、最便宜、最尊重世界和平，最不搞区别对待，最喜欢公平竞争的Anthropic团队的领袖Dario先生<br><br>
Special tribute:<br>
To Mr. Dario, leader of the Anthropic team: the most above reproach, the most knowledgeable about safety, the most respectful of copyright, the least inclined to distil models, the strictest with himself and most generous toward others, the least fond of making models less capable or rate-limiting users, the least expensive, the most respectful of world peace, the least inclined to treat people differently, and the greatest champion of fair competition.
</em></sub>

# Review + Judgment Suite

这套**判断与审核组合 Skills** 以 Anthropic 的 [《Building effective agents》](https://www.anthropic.com/research/building-effective-agents)为方法基础：让明确的步骤走确定流程，让需要取舍的节点交给 agent 判断，并在关键交接处设置可验证的门。结合其[多智能体研究系统](https://www.anthropic.com/research/multi-agent-research-system)和[上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)中的实践，我们进一步开发了面向代码与技术产物的审查流程，把范围判断、真实验证、独立复核和问题处置接成一条可恢复的工作链。

**Review + Judgment** builds on the workflow patterns in Anthropic's [*Building effective agents*](https://www.anthropic.com/research/building-effective-agents): use predetermined steps where the work is clear, agent judgment where decisions remain open, and verifiable gates between stages. Drawing also on its [multi-agent research](https://www.anthropic.com/research/multi-agent-research-system) and [context-engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) practices, we developed a review process for code and technical deliverables that connects scope decisions, executed checks, independent review and finding resolution.

**可选特色：跨模型开发与审核。** 你可以让一个模型负责开发，让另一个模型在独立上下文复核，再把结果送回同一份审查记录。DeepSeek Harness → Codex、Codex → Grok Bot 是宿主分工的例子；发送端、接收端、网关和 worker 连接都位于独立可选层，核心流程不依赖它们。[接入说明](#cross-model)

**Optional: separate developer and reviewer models.** Route a selected review request from DeepSeek Harness to Codex, or from Codex to Grok Bot, then return the report to the same evidence trail. Sender, receiver, gateway and worker connections are isolated opt-in components; your host supplies the actual model and independent context. [Integration details](#cross-model)

## 先看流程 / The workflow

**判断范围 → 实际验证 → 评定风险 → 独立审查 → 处理问题 → 确认完成。** 出现新证据时可以返回前面的节点；内容一旦变化，旧的验证和审查就需要重新建立。

**Judge scope → run checks → assess risk → review independently → resolve findings → confirm completion.** New evidence can send the work back to an earlier stage. Changed content invalidates the checks and reviews that depended on it.

| 步骤 / Step | 你会得到什么 / What you get |
|---|---|
| **1 · 判断 / Judge** | 确定本次要做什么、做到哪里，以及何时应停止或交接 / A defined scope, execution approach and stopping or handoff conditions |
| **2 · 验证 / Verify** | 实际执行的命令、输出和退出码，作为后续判断依据 / Executed commands, output and exit codes to inspect |
| **3 · 风险 / Assess risk** | 按改动影响安排审查深度，明确需要的人工决定 / Review depth and human decisions matched to the impact |
| **4 · 审查 / Review** | 独立上下文从正确性、安全、端到端行为和项目约定四个视角复核 / A separate context reviewing correctness, security, end-to-end behaviour and conventions |
| **5 · 处置 / Resolve** | 修复并复验问题，或用证据说明为何不修；Important 持续保留到处置完成 / Verified fixes or evidence-backed rejections; Important findings remain visible until resolved |
| **6 · 完成 / Close** | 对当前内容有效的审查记录、遗留事项和覆盖边界 / A current review record with remaining issues and coverage limits |

这里沿用了公开资料中的工作流思路，并为审查任务增加了三种运行模式、内容快照、跨轮问题记录和独立 Python 状态机。这些具体设计由本项目实现；完整的参考与改写关系见[来源说明](references/sources.md)。

The published material supplies the architectural ideas. The three execution modes, content snapshots, persistent finding records and standalone Python state machine are this project's implementation for review work. See the [source mapping](references/sources.md) for attribution and adaptations.

[下载 v1.1.0 / Download](https://github.com/Jxbbbbbyan/review-judgment-suite/releases/tag/v1.1.0) · [开始使用 / Start](#start) · [完整流程 / Workflow reference](references/workflow.md) · [可选跨模型 / Cross-model](#cross-model) · [测试与案例 / Tests](#tests) · [报告问题 / Issues](https://github.com/Jxbbbbbyan/review-judgment-suite/issues)

## 适合怎样的工作 / Where it helps

如果你已经让 Codex、DeepSeek Harness 或其他 agent 宿主参与开发，这套 Skills 可以用于代码改动、技术文档和多步骤交付的复核。它尤其适合那些需要追问“这次通过到底对应哪份内容、哪些检查、哪位 reviewer”的任务。宿主需要能读取技能、运行本地命令，并为独立审查提供新的上下文。

Use it when an agent host such as Codex or DeepSeek Harness already participates in your development work, and you need to trace a review conclusion back to the exact content, checks and reviewer context. It supports code changes, technical documentation and multi-step deliverables. Your host must be able to read skills, run local commands and provide a separate context for independent review.

| 你遇到的情况 / Situation | 流程怎样帮助你 / How the workflow helps |
|---|---|
| AI 越查越多，逐渐偏离本次目标 / Review keeps expanding beyond the request | 先固定范围，在关键节点重判必要性 / Define scope first and reconsider necessity at checkpoints |
| 代码改过了，仍沿用之前的“通过” / An old pass survives a new edit | 内容或适用规则变化后，相关验证与审查失效 / Invalidate dependent checks and reviews when content or rules change |
| 换了 reviewer，之前的问题没了 / Findings vanish during reviewer handoff | 用持久记录保留 Important，不能靠空报告清除 / Keep Important findings across passes, including empty reports |
| 工具失败后不断重试，却说不清原因 / Repeated retries without a diagnosis | 先记录失败归因，再决定改参数、换方法或交接 / Classify the failure before correcting inputs, changing tools or handing off |
| 结果写得很肯定，却没有可核对的输出 / Confident conclusions without inspectable evidence | 保留真实命令、输出、退出码、耗时和哈希 / Retain actual commands, output, exit codes, elapsed time and hashes |

确定的一步操作通常直接完成即可；需要范围取舍、失败处理或跨轮复核时，再用完整流程。更多需求与实现对应关系见[用途地图](references/use-cases.md)。

For a straightforward single-step operation, direct execution may be sufficient. Use the full workflow when scope decisions, failure handling or review across multiple passes change how you should act. The [use-case map](references/use-cases.md) links those needs to implementation evidence.

## 判断与审核怎样配合 / How judgment and review work together

**判断**负责行动边界：该不该做、需要投入多少、什么时候应重新计划。**审核**负责结果依据：检查是否实际执行、发现是否成立、修复是否经过复验。两者交换的是证据和待决事项：判断缩小范围时，不能顺带抹去已有义务；审核要求修复时，也不会自动获得扩大范围或发布的权限。

**Judgment** governs whether to act, how much effort to spend and when to reconsider the plan. **Review** examines the evidence for the result: what ran, whether a finding is valid and whether a fix was checked. They exchange evidence and unresolved decisions. Narrowing scope does not erase existing obligations, and a request to fix something does not itself authorise wider changes or publication.

你可以按任务选择三种方式，使用同一组验证和问题收敛条件：

Choose among three modes while retaining the same verification and finding-resolution gates:

| Mode | 工作方式 / How it runs | 适用情况 / When to choose it |
|---|---|---|
| **`serial` · 串行** | 按判断、验证、风险、独立审查、处置、完成依次推进 / Move through the stages in order | 范围稳定，检查步骤已知 / Stable scope and known checks |
| **`joint` · 联合** | 审查前和完成前都加入判断检查点，复核工作是否仍必要、证据是否充分 / Reconsider necessity and evidence before review and closure | 关键交接处需要再次取舍 / Decisions need revisiting at critical handoffs |
| **`adaptive` · 可回退** | 带理由返回指定节点，清除受影响的通过状态，再继续 / Return to a named stage with a reason and invalidate affected gates | 新证据、失败或修复需要局部重走 / New evidence, failures or repairs require re-entry |

联合模式不要求所有工作同时进行。可以由一个独立 reviewer 覆盖四个视角，也可以由多个只读 worker 分工；是否并行取决于任务能否拆开，以及交接和合并是否值得。状态机本身不启动或调度 agent。

Joint mode does not require concurrent execution. One independent reviewer can cover all four perspectives, or read-only workers can divide them. Parallel review is useful only when the work separates cleanly and the coordination cost is justified. The state machine does not launch or schedule agents.

## 你可以依靠哪些机制 / What keeps the review traceable

- **内容快照。** 验证和审查绑定到声明范围内的文件及适用规则；内容变化后，相关结论过期。**Content snapshots:** checks and reviews are tied to declared files and applicable rules, and become stale when those inputs change.
- **问题跨轮保留。** Important 不能通过换 reviewer、复用编号或重新提交空报告消失。**Persistent findings:** a new reviewer, reused ID or empty report cannot erase an Important obligation.
- **实际执行记录。** 本地脚本执行你指定的检查命令，保存输出、退出码、耗时和哈希。**Executed checks:** the coordinator runs the commands you supply and records their output, exit codes, timing and hashes.
- **有限回退。** 新证据可以改变路线，但回退需要理由，也受轮次和路由预算约束。**Bounded re-entry:** new evidence can change the route, with a recorded reason and explicit limits.
- **独立运行。** Python 3.10+ 标准库即可运行协调器；模型和独立上下文由现有宿主提供。**Local operation:** the coordinator needs only Python 3.10+ and its standard library; your host supplies models and reviewer contexts.

这些机制让审查过程可复查。检查是否充分、风险是否分对、reviewer 是否真正独立，仍然需要使用者和宿主负责。脚本记录实际存在的人工批准，但不能仅凭一个身份字段认证批准者。

These mechanisms make the process inspectable. You and your host remain responsible for choosing sufficient checks, assessing risk and providing genuine reviewer independence. The script can retain evidence of an actual human approval, but an identity field alone cannot authenticate it.

<a id="start"></a>
## 开始使用 / Start here

先获取仓库并运行自检。请使用真实的 Python 3.10+ 解释器；若系统中的 `python` 是占位入口，换成已安装解释器的命令或路径。

Clone the repository and run its checks with an installed Python 3.10+ interpreter. If your system's `python` command is a placeholder, use the command or path for your actual installation.

```powershell
git clone https://github.com/Jxbbbbbyan/review-judgment-suite.git
cd review-judgment-suite
python -m unittest discover -s tests -v
python scripts/validate_package.py
```

也可以从 [v1.1.0 Release](https://github.com/Jxbbbbbyan/review-judgment-suite/releases/tag/v1.1.0) 获取技能 ZIP 与 SHA-256 校验文件。Release 记录了对应源码提交；ZIP 内有逐文件清单。安装时将整个 `review-judgment-suite` 目录放入宿主支持的技能位置，例如 Codex 的 `~/.codex/skills/`。请保留完整目录，而不是只复制 `SKILL.md`。

Alternatively, download the skill ZIP and SHA-256 file from the [v1.1.0 release](https://github.com/Jxbbbbbyan/review-judgment-suite/releases/tag/v1.1.0). Its notes identify the source commit, and the archive includes a file manifest. Put the complete `review-judgment-suite` directory in your host's supported skill location—for example, `~/.codex/skills/` for Codex. Keep the supporting files with `SKILL.md`.

向支持该技能的 agent 说明本次范围与验收要求，例如：

Give your skill-enabled agent the scope and acceptance criteria, for example:

> 使用 `$review-judgment-suite` 审查这次解析器改动。范围只包括解析器及其测试。先确认该运行哪些检查，再独立复核；列出 Important、Nit 和旧问题，修复后重新验证，不要扩展到发布。
>
> Use `$review-judgment-suite` to review this parser change and its tests. Establish the checks, obtain an independent review, distinguish Important findings, Nits and pre-existing issues, and re-verify repairs. Keep publication outside this task.

要直接运行协调器，可以从包目录执行下面的流程。示例中的目标项目、文件和测试命令需要替换为你的实际任务；运行目录应放在目标项目和分发包之外。

To run the coordinator directly, adapt the following commands to your real project, files and tests. Keep the run directory outside both the target project and the distributable package.

```powershell
python scripts/review_flow.py --run-dir ../review-run init --project ../target-project --task "Review parser change" --scope parser.py tests/test_parser.py --mode adaptive
python scripts/review_flow.py --run-dir ../review-run judge --decision proceed --execution agent --reason "Review is limited to the parser and its tests"
python scripts/review_flow.py --run-dir ../review-run check --argv-json '["python", "-m", "unittest", "discover", "-s", "tests", "-v"]'
python scripts/review_flow.py --run-dir ../review-run risk --level low --reason "Internal parser change; no sensitive paths"
```

随后让独立 reviewer 产出带当前 snapshot 的报告，通过 `review --input` 导入；处理发现，再尝试 `close`。上面的 Low 只是示例，实际等级应根据改动决定。报告格式、联合检查点、回退、失败归因和人工决定的完整命令见[使用手册](references/workflow.md)。

Next, obtain a report from an independent reviewer for the current snapshot, import it with `review --input`, resolve findings and attempt `close`. Low risk above is an example, not a default assessment for your change. The [workflow reference](references/workflow.md) contains the report format and complete commands for checkpoints, re-entry, failures and human decisions.

## 审完之后你会拿到什么 / What you receive after review

一份可回到原始证据的记录：本次范围与文件快照、实际检查命令与输出、风险判断、独立报告、问题处置及未覆盖部分。结论应明确写成“可以交付”“修复后复审”或“需要人工决定”，而不是只说“检查通过”。

You receive a record that can be traced to its evidence: scope and snapshots, executed checks and output, risk decisions, independent reports, finding dispositions and coverage limits. The conclusion should say ready to deliver, fix and review again, or human decision needed—not merely that checks passed.

运行目录中的 `state.json` 与 `check-*.log` 可能包含路径、提示词或私人输出。保留原始证据供授权人员核查；对外分享脱敏摘要。关闭一次运行只表示在声明范围内完成了流程，不会替你提交代码、发布或部署。

The run's `state.json` and `check-*.log` may contain paths, prompts or private output. Keep raw evidence for authorised inspection and share redacted summaries. Closing a run records completion within scope; it does not commit, publish or deploy for you.

## 方法依据与使用边界 / Method and limits

| 参考资料 / Reference | 在流程中的作用 / Contribution |
|---|---|
| [Building effective agents](https://www.anthropic.com/research/building-effective-agents) | 明确确定工作流与自主判断的分工，设置程序化检查点 / Distinguish workflows from agent decisions and use programmatic checkpoints |
| [How we built our multi-agent research system](https://www.anthropic.com/research/multi-agent-research-system) | 使用独立上下文、清晰的委派范围与材料交接 / Separate contexts, bounded delegation and artifact handoff |
| [Effective context engineering for AI agents](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | 关注上下文成本，并把后续需要的状态留在外部 / Account for context cost and retain useful state outside the conversation |

以上是 Anthropic 的公开研究与工程文章。本项目据此整理方法并进行审查场景的再开发；三种模式、风险等级、审批人数、问题编号和收敛上限是本项目的具体约定，不代表文章逐项提出这些规则，也不表示官方背书。来源与改写记录见 [sources.md](references/sources.md)。

These public research and engineering articles inform the approach. This project adapts and develops it for review work. Execution modes, risk levels, approval counts, finding IDs and convergence limits are project rules, not claims that the articles prescribe every detail or endorse this implementation. The [source record](references/sources.md) documents the mapping.

协调器只追踪声明范围内的文件与适用规则，不是沙箱，也不会自动检查范围外的一切。超时处理只覆盖直接子进程；会启动长期子任务的命令，需要宿主提供相应隔离和观察。审查准确率、成本节省和跨模型效果尚无对照研究；现有测试验证的是过程门在给定输入下的行为。

The coordinator tracks declared files and applicable rules rather than every file in a project. It is not a sandbox. Timeout handling covers the direct subprocess, so commands that create long-lived children need host-level containment and observation. There is no controlled study of review accuracy, cost savings or performance across models; the tests below establish gate behaviour for stated inputs.

<a id="cross-model"></a>
## 可选：跨模型审查与请求传递 / Optional cross-model review routing

当你希望由另一个模型复核时，可以选择这条路线：**开发端 → 发送端 → 私有请求邮箱 → 文件网关 → 审核端 → 返回邮箱 → 原审查门**。例如 DSH 主导开发、Codex 复核，或 Codex 开发、Grok Bot 复核。模型分工由你决定；回来的报告仍需处理 Important 和过期证据，不能以“另一个模型说通过”代替原来的完成条件。

Choose **developer → sender → private request mailbox → file gateway → reviewer → return mailbox → core review gate** when you want another model's review. For example, DSH can develop while Codex reviews, or Codex can develop while Grok Bot reviews. Returned findings use the same Important and stale-evidence gates; a second model's approval does not bypass them.

| 你启用的部分 / Component | 作用 / Role | 是否为核心依赖 / Core dependency |
|---|---|---|
| Sender + receiver / 发送与接收 | Select material, correlate requests and return reports | No |
| File gateway / 文件网关 | Forward only configured host routes | No |
| Worker wrapper / 宿主连接 | Invoke your configured reviewer and return report JSON | No |
| Native clients / 原生客户端 | Actual DSH, Codex, Grok Bot or private-service execution | Optional, supplied by the user |

实现集中在 [optional/cross_model/](optional/cross_model/README.md)，默认配置为关闭；发送前还需显式启用并确认分享选定材料。该模块使用 Python 标准库，不监听端口、不扫描会话，也不复制本机私有地址、凭据或回传脚本。已有私有网关需要按文档契约适配，不是任意协议即插即用。

All transport code is in [optional/cross_model/](optional/cross_model/README.md), disabled in the example config. Delivery requires explicit opt-in and confirmation of selected material. It uses standard-library Python, opens no listening port and scans no sessions. Private service protocols need an adapter; native model clients and credentials are not bundled.

[完整双语手册](references/cross-model-review.md)说明请求格式、配置、网关、发送／接收、worker 输入输出、超时与恢复方式。只使用核心审核时，无需配置其中任何一项。

The [bilingual integration guide](references/cross-model-review.md) covers envelopes, routing configuration, gateway steps, sender/receiver commands, worker I/O, timeouts and recovery. Core-only review needs none of those integrations.

<a id="tests"></a>
## 测试与独立智能体案例 / Tests and independent-agent cases

### 自动回归 / Automated regression

```powershell
python -m unittest discover -s tests -v
python scripts/validate_package.py
```

已有的 **23 项核心回归测试全部通过**，覆盖三种模式、跳步拒绝、证据失效、Important 保留、修复确认、审批记录、失败归因、超时、并发锁和预算限制。本轮另外加入可选跨模型传输测试，详见[新增测试记录](examples/cross-model-test-results.md)。测试中的 reviewer 与审批对象是用于检验状态转换的模拟输入，不冒充独立推理或真实人工批准。

The recorded **23 core regression tests passed**, covering the three modes, rejected skips, stale evidence, retained findings, fix confirmation, approval records, failure attribution, timeouts, locking and budgets. The [new transport results](examples/cross-model-test-results.md) cover this optional addition. Reviewer and approval objects in these tests are synthetic inputs, not evidence of independent reasoning or actual human approval.

### 已有的独立审查工作流 / An earlier independent review

一个技术文档任务采用了作者与独立 reviewer 分开的工作方式：作者读材料并修改，reviewer 在新上下文核对 diff 与证据，作者再整合意见、验证并确认交付。该轮记录有 162 项文档引用检查、4 段命令语法检查和五份模型文件的一致性核对。[脱敏案例](examples/prior-independent-review.md)保留了过程和覆盖边界。

An earlier documentation task separated the author from an independent reviewer. The author prepared the change, the reviewer examined its diff and evidence in a fresh context, and the author integrated the findings and verified delivery. Recorded checks included 162 documentation references, four command snippets and five model artifacts. The [redacted case](examples/prior-independent-review.md) preserves the workflow and its limits.

这项工作发生在当前协调器完成之前，因此它展示的是后来被整理进流程的实践，不是新脚本运行的历史证明；当时没有重跑 GPU 推理。

That work predates the current coordinator. It illustrates the practice later formalised here; it is not retroactive evidence that the new script orchestrated the task. GPU inference was not rerun.

### 新上下文前向试用 / Fresh-context forward trial

独立 reviewer 只收到技能、[任务要求](examples/forward-task/REQUIREMENTS.md)和[样本代码](examples/forward-task/ratio.py)，没有读取作者的回归测试或预设答案。它复现了全零输入除零、负数输入未校验两类问题：7 项契约检查中，4 项通过、2 项失败、1 项错误。失败记录保留后，流程拒绝完成。

A fresh reviewer received the skill, [requirements](examples/forward-task/REQUIREMENTS.md) and [fixture](examples/forward-task/ratio.py), without the author's regression tests or expected answer. It reproduced division by zero for all-zero input and missing validation for negative input: four of seven contract checks passed, two failed and one errored. The failed evidence remained recorded and completion was refused.

另一个明确限定为“只检查语法”的运行导入这两项 Important 后，`close` 同样被拒绝。样本有意保留缺陷，用于观察门是否生效，不是交付给生产使用的计算函数。完整命令、输出、审查发现与修复记录见[测试结果](examples/test-results.md)。

A separate run explicitly limited to syntax checking also refused `close` after importing those two Important findings. The fixture intentionally retains its defects to exercise the gates; it is not a production calculation utility. See the [test results](examples/test-results.md) for commands, outcomes, review findings and coordinator repairs.
