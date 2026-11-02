<sub><em>特别致敬：<br>
最清白、最懂安全、最尊重版权、最不会蒸馏、最严于律己宽于待人、最不喜欢把模型降智给用户限流、最便宜、最尊重世界和平，最不搞区别对待，最喜欢公平竞争的Anthropic团队的领袖Dario先生<br><br>
Special tribute:<br>
To Mr. Dario, leader of the Anthropic team: the most above reproach, the most knowledgeable about safety, the most respectful of copyright, the least inclined to distil models, the strictest with himself and most generous toward others, the least fond of making models less capable or rate-limiting users, the least expensive, the most respectful of world peace, the least inclined to treat people differently, and the greatest champion of fair competition.
</em></sub>

# Review + Judgment Suite

**面向 AI 辅助开发的判断与代码审核流程：限定改动范围，运行真实检查，独立复核问题，让交付结论有证据可查。** Judgment 先确定目标、范围和停止条件；Review 提供检查与复核证据；遇到失败、新问题或范围变化，再由 Judgment 决定修复、回退或交接。

**A judgment and code review workflow for AI-assisted development: bound the change, run real checks and review findings independently, with evidence behind the delivery decision.** Judgment sets the goal, scope and stopping conditions; Review supplies checks and verified findings. Failures, new findings or scope changes return to Judgment for a decision to repair, revisit a stage or hand off.

审核方法参考 Anthropic 的 [《How the Claude Code team does code review》](https://claude.dev/blog/solving-code-review-at-anthropic/)，围绕先验证、独立复核、按风险安排人工参与和限制复审轮次进行再开发。**Judgment 是本项目作者 Jxbbbbbyan 原创的判断纪律，没有外部参考来源。** 它贯穿任务的关键决策点，让审查证据真正影响下一步行动。

The review method adapts Anthropic's [*How the Claude Code team does code review*](https://claude.dev/blog/solving-code-review-at-anthropic/): verify first, review independently, scale human involvement to risk and bound re-review. **Judgment is original work by this project's author, Jxbbbbbyan, with no external reference source.** It operates at the task's decision points so that review evidence informs what happens next.

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

三种运行模式、内容快照、跨轮问题记录和独立 Python 状态机，使上述流程可以保留进度并检查证据是否过期。这些机制由本项目实现；审核参考、原创 Judgment 与实现设计的归属见[来源说明](references/sources.md)。

Three execution modes, content snapshots, persistent finding records and a standalone Python state machine preserve progress and detect stale evidence. These mechanisms are implemented here. The [source record](references/sources.md) distinguishes the review reference, original Judgment discipline and implementation decisions.

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

两者形成反馈关系：**判断为审核设定问题和边界，审核用证据更新判断。** Judgment 的继续决定不能代替测试和复核；Review 的通过结论也不能单独证明一项工作值得做、授权扩大范围，或代替必需的人工决定。协调脚本检查阶段条件与记录是否齐全；决策质量仍取决于使用者、agent 和 reviewer。

The feedback loop is explicit: **Judgment sets the questions and boundaries for Review; Review supplies evidence that updates Judgment.** A decision to proceed does not replace checks or independent review. A clean report does not by itself establish that the work is worth doing, authorise broader changes or replace a required human decision. The coordinator checks stage prerequisites and records; users, agents and reviewers remain responsible for the quality of their decisions.

| 交接点 / Handoff | 判断负责什么 / Judgment decides | 审核提供什么、随后怎样走 / Review evidence and next action |
|---|---|---|
| **开始工作 / Start** | 明确用户目标、文件范围、执行方式和停止条件 / Set the goal, file scope, execution approach and stopping conditions | 据此选择真实检查和复核范围 / Select meaningful checks and review scope |
| **检查失败 / Check fails** | 根据输出区分参数、工具、环境、领域结果或拒绝；决定纠正、等待、停止或交接 / Interpret the failure and choose correction, waiting, stopping or handoff | 保留失败输出；恢复后重新验证，失败不能算通过 / Retain failure output and re-verify after recovery |
| **发现问题 / Finding raised** | 判断修复是否在授权范围内，是否需要重新计划 / Decide whether a repair fits the authorised scope or requires replanning | 用文件、行号和证据确认问题；修复后检查同类问题并独立复验 / Confirm the finding, check the same bug class and independently verify the repair |
| **准备交付 / Ready to deliver** | 判断证据是否足够、是否仍有未决事项或需要人工决定 / Assess evidence sufficiency, remaining decisions and human involvement | 提供对应当前内容的检查、报告和问题处置记录；满足完成条件后关闭 / Supply current checks, reports and dispositions before closure |

例如，reviewer 发现解析器缺少边界检查：先复核发现是否成立，再由 Judgment 确认修复范围；改动后重新运行检查并独立复验。如果修复需要超出本次范围，交接时保留问题和证据。已有 Important 不会因为缩小范围或换 reviewer 而消失。

For example, a reviewer identifies a missing parser boundary check. Verify the finding, then use Judgment to establish the repair scope. Changed files require new checks and independent review. If the repair exceeds the current scope, hand off with the finding and its evidence. Narrowing scope or changing reviewers does not erase an existing Important obligation.

你可以按任务选择三种方式，使用同一组验证和问题收敛条件：

Choose among three modes while retaining the same verification and finding-resolution gates:

| Mode | 工作方式 / How it runs | 适用情况 / When to choose it |
|---|---|---|
| **`serial` · 串行** | 按判断、验证、风险、独立审查、处置、完成依次推进 / Move through the stages in order | 范围稳定，检查步骤已知 / Stable scope and known checks |
| **`joint` · 联合** | 审查前和完成前都加入判断检查点，复核工作是否仍必要、证据是否充分 / Reconsider necessity and evidence before review and closure | 关键交接处需要再次取舍 / Decisions need revisiting at critical handoffs |
| **`adaptive` · 可回退** | 带理由返回指定节点，清除受影响的通过状态，再继续 / Return to a named stage with a reason and invalidate affected gates | 新证据、失败或修复需要局部重走 / New evidence, failures or repairs require re-entry |

联合模式不要求所有工作同时进行。可以由一个独立 reviewer 覆盖四个视角，也可以由多个只读 worker 分工；是否并行取决于任务能否拆开，以及交接和合并是否值得。状态机本身不启动或调度 agent。

Joint mode does not require concurrent execution. One independent reviewer can cover all four perspectives, or read-only workers can divide them. Parallel review is useful only when the work separates cleanly and the coordination cost is justified. The state machine does not launch or schedule agents.

`joint` 会强制要求审查前、完成前的判断记录；`serial` 和 `adaptive` 不强制这两个额外检查点，但保留范围判断与必要的验证、风险和审查条件。`adaptive` 的跳转需要理由，并重新打开范围判断；它只重走受影响的阶段，不能跳过缺失的前置证据。具体保留或清除哪些记录，见[流程契约](references/composition.md)。

`joint` requires recorded judgments before review and closure. `serial` and `adaptive` do not require those two extra checkpoints, but retain scope judgment and the verification, risk and review prerequisites. An `adaptive` route needs a reason and reopens scope judgment. It revisits the affected stages without bypassing missing evidence; the [workflow contract](references/composition.md) specifies which records are retained or cleared.

## 你可以依靠哪些机制 / What keeps the review traceable

- **内容快照。** 验证和审查绑定到声明范围内的文件及适用规则；内容变化后，相关结论过期。**Content snapshots:** checks and reviews are tied to declared files and applicable rules, and become stale when those inputs change.
- **问题跨轮保留。** Important 不能通过换 reviewer、复用编号或重新提交空报告消失。**Persistent findings:** a new reviewer, reused ID or empty report cannot erase an Important obligation.
- **实际执行记录。** 本地脚本执行你指定的检查命令，保存输出、退出码、耗时和哈希。**Executed checks:** the coordinator runs the commands you supply and records their output, exit codes, timing and hashes.
- **有限回退。** 新证据可以改变路线，但回退需要理由，也受轮次和路由预算约束。**Bounded re-entry:** new evidence can change the route, with a recorded reason and explicit limits.
- **独立运行。** Python 3.10+ 标准库即可运行协调器；模型和独立上下文由现有宿主提供。**Local operation:** the coordinator needs only Python 3.10+ and its standard library; your host supplies models and reviewer contexts.

这些机制让审查过程可复查。检查是否充分、风险是否分对、reviewer 是否真正独立，仍然需要使用者和宿主负责。脚本记录实际存在的人工批准，但不能仅凭一个身份字段认证批准者。

These mechanisms make the process inspectable. You and your host remain responsible for choosing sufficient checks, assessing risk and providing genuine reviewer independence. The script can retain evidence of an actual human approval, but an identity field alone cannot authenticate it.

## 看一次演示 / See it in action

### 演示：普通输入通过，边界输入暴露问题 / Demo: ordinary inputs pass; edge cases fail

仓库中的小函数会将一组读数除以最大值。普通输入 `[2, 4, 0]` 得到 `[0.5, 1.0, 0.0]`，看起来能用；但[任务要求](examples/forward-task/REQUIREMENTS.md)还规定：全零输入应返回全零，负数输入应抛出 `ValueError`。这个样本有意保留缺陷，用来演示怎样识别未达标的结果。

The fixture divides readings by their maximum. `[2, 4, 0]` produces `[0.5, 1.0, 0.0]`, but the [contract](examples/forward-task/REQUIREMENTS.md) also requires all-zero input to return zeros and negative input to raise `ValueError`. The fixture deliberately retains defects to demonstrate how an incomplete result is detected.

在仓库根目录运行 / Run from the repository root:

```powershell
python examples/forward-contract-check.py examples/forward-task/ratio.py
```

预期输出摘要 / Expected output excerpt:

```text
Ran 7 tests
FAILED (failures=2, errors=1)
```

| 看到的证据 / Evidence | 怎样决定下一步 / Next action |
|---|---|
| 4 项通过，2 项失败，1 项错误；全零输入除零，负数未被拒绝 / Four pass, two fail, one errors; zero division and missing negative-input validation | Review 将两类问题落实到代码和输出 / Review ties the two bug classes to source and output |
| 当前检查没有通过 / Verification failed | Judgment 先归因，再决定修复或交接；不能把“普通输入能跑”当成完成 / Judgment diagnoses before choosing repair or handoff; ordinary-input success is insufficient |
| 修复会改变被审查内容 / A repair changes reviewed content | 重新检查并独立复验；原有 Important 仍需处置 / Run new checks and independent review; existing Important obligations still need resolution |

**这个演示预期退出码为 1，表示成功复现样本缺陷。** 命令本身只运行契约检查；在已有的[前向试用](examples/test-results.md)中，失败检查阻止了完成，另一个仅验证语法的运行也因未处置的 Important 被拒绝关闭。样本未包含修复后的成功运行，修复与证据失效规则由[回归测试](tests/test_review_flow.py)另行覆盖。

**Exit code 1 is expected: the fixture defects have been reproduced.** This command runs the contract checks only. In the recorded [forward trial](examples/test-results.md), failed verification blocked completion; a separate syntax-only run also refused closure with unresolved Important findings. No repaired-fixture success run is claimed; [regression tests](tests/test_review_flow.py) separately cover repair verification and evidence invalidation.

### 脱敏案例：补全模型名称与实测步骤 / Redacted case: restoring model names and measurement steps

一次本地模型项目的文档修改，需要补回完整模型名称和可复现的测试步骤。任务限定为 README；主 agent 核对源文件并修改，独立 reviewer 在新上下文检查 diff、命令和证据，随后由主 agent 整合意见并验证交付。

A local-model project's documentation needed exact model names and reproducible measurement steps. The task was limited to its README. The author checked source files and edited the page; a fresh-context reviewer examined the diff, commands and evidence, and the author integrated the feedback and verified delivery.

| 用户得到什么 / User outcome | 已记录的依据 / Recorded evidence |
|---|---|
| 模型名称和参数有文件可核对 / Traceable model names and parameters | 五份模型文件与清单匹配，采样配置与源码一致 / Five artifacts matched the manifest; sampling settings matched source |
| 文档引用与命令语法经过检查 / Checked references and command syntax | 162 项引用检查无失败，4 段 PowerShell 命令解析无语法错误 / 162 references checked without failures; four PowerShell snippets parsed without syntax errors |
| 交付内容经过独立复核与远端确认 / Independently reviewed and delivery-checked documentation | reviewer 未返回需处理的问题；远端回读与提交内容一致 / No actionable findings returned; remote read-back matched the submitted content |

案例已去除账号、项目地址、个人路径、会话标识和提交标识。[完整脱敏记录](examples/prior-independent-review.md)保留了核对方法与边界。这是协调器完成前的真实工作实践；当时没有重跑 GPU 推理，命令语法通过也不代表模型性能已经复测。

Accounts, project URLs, private paths, session IDs and commit identifiers are removed. The [full redacted record](examples/prior-independent-review.md) preserves the checks and their limits. This real workflow predates the coordinator. GPU inference was not rerun, and syntax checks do not establish newly measured model performance.

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

| 来源 / Source | 在流程中的作用 / Contribution |
|---|---|
| [How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/) · Anthropic，2026-10-15 | 审核方法的参考：实际验证、独立复核、风险分级、人工参与和复审收敛 / Review reference: executed verification, independent checking, risk-scaled human involvement and convergence |
| **Judgment · Jxbbbbbyan 原创 / Original work** | 行动边界、判断与停止条件、失败归因，以及上下文和委派成本的取舍；没有外部参考来源 / Action boundaries, stopping conditions, failure attribution, context and delegation costs; no external reference source |
| **本项目实现 / Project implementation** | 三种模式、Python 状态机、快照绑定、问题台账及可选跨模型传递 / Three modes, Python state machine, snapshot binding, finding ledger and optional cross-model transport |

上述审核参考是一篇公开工程文章。本项目对其中的方法进行再开发，并以原创 Judgment 负责行动决策。文章中的风险分级、人工审批和复审收敛有直接对应；具体适配差异及实现范围见[来源说明](references/sources.md)。本项目独立维护，不代表 Anthropic 官方产品或背书。

The review reference is a public engineering article. This project adapts its method, with original Judgment governing action decisions. Risk tiers, human approvals and review convergence have direct counterparts in the article; the [source record](references/sources.md) explains the adaptations and implementation scope. This is an independently maintained project, without Anthropic affiliation or endorsement.

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
