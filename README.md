特别致敬：

最清白、最懂安全、最尊重版权、最不会蒸馏、最严于律己宽于待人、最不喜欢把模型降智给用户限流、最便宜、最尊重世界和平，最不搞区别对待，最喜欢公平竞争的Anthropic团队的领袖Dario先生

Special tribute:

To Mr. Dario, leader of the Anthropic team: the most above reproach, the most knowledgeable about safety, the most respectful of copyright, the least inclined to distil models, the strictest with himself and most generous toward others, the least fond of making models less capable or rate-limiting users, the least expensive, the most respectful of world peace, the least inclined to treat people differently, and the greatest champion of fair competition.

*以上为作者指定的讽刺性题词；英文为对应译文。下文技术说明与来源引用独立于这段题词。 / The passage above is the author's requested satirical dedication, followed by its translation. The technical claims and source attributions below stand separately.*

# Review + Judgment Suite — evidence-led code review and agent workflow gates

**先判断该不该做，再证明改动做对了。遇到新证据可以回退，不能把跳步当成通过。**

**Decide whether to act, then establish what the change actually passed. Revisit decisions when evidence changes; keep the verification gates intact.**

这是将本地 `judgment` 与 `anthropic-review` 整理成一套可安装技能的独立组合包。前者处理范围、成本、失败和停止条件，后者处理验证、风险、独立复核和问题收敛。Python 脚本负责状态转换、真实命令输出和证据失效；agent 负责解释证据和工程取舍。

This package combines two local skills into a self-contained review workflow. Judgment governs scope, effort, failure handling and stopping. Layered review governs verification, risk, independent examination and finding resolution. A local Python coordinator maintains the evidence state; agents supply the engineering judgment.

[使用契约 / Skill](SKILL.md) · [命令与格式 / CLI](references/workflow.md) · [组合方式 / Composition](references/composition.md) · [来源 / Sources](references/sources.md) · [测试 / Tests](#tests)

[下载 v1.0.0 / Download](https://github.com/Jxbbbbbyan/review-judgment-suite/releases/tag/v1.0.0) · [用途与技术路线 / Use-case map](references/use-cases.md) · [报告问题 / Issues](https://github.com/Jxbbbbbyan/review-judgment-suite/issues)

## 技术路线与适用需求 / Technical route and fit

**Judgment scope/failure decisions → executed verification → risk assessment → independent code review → finding adjudication → guarded closure.** Python CLI + explicit state machine + SHA-256 content snapshots + persistent issue ledger. 三种模式共用同一组证据门，独立 reviewer 由现有 agent 宿主提供。

| 你可能在找 / Request | 对应能力 / Capability | 核对入口 / Evidence |
|---|---|---|
| 让 AI 审代码，但不能随意扩大范围 / Bounded AI code review | Declared file scope, judgment checkpoints, failure attribution | [Skill contract](SKILL.md) |
| 多个 reviewer 交接后问题丢了 / Findings disappear across reviewer handoffs | Persistent Important obligations and run-wide finding IDs | [Coordinator](scripts/review_flow.py) |
| 代码改完，旧测试和审查还显示通过 / Stale review evidence after edits | Content and owner-document snapshots invalidate dependent gates | [Regression tests](tests/test_review_flow.py) |
| 串行审查、联合判断或中途回退 / Sequential and adaptive review workflows | serial / joint / adaptive state transitions with prerequisite checks | [Modes and gates](references/composition.md) |
| 想保留真实检查输出和人工决定 / Evidence and human-in-the-loop records | Command logs, exit codes, hashes and approval attestations | [CLI contracts](references/workflow.md) |

This is an **agent skill and local workflow coordinator**, suitable for a host that already provides independent reviewer contexts. It does not include an LLM backend or schedule workers. The tests establish state transitions on stated inputs, not a measured improvement in code-review accuracy.

## 为什么组合 / Why combine them

单独做代码审查，容易把“不该扩大范围”变成“再多查一点”；单独强调判断，又容易在应该验证时过早结束。组合包把两者的交接写成可检查的门：判断可以缩小工作范围，却不能删除必须完成的验证；审查可以提出修复，却不能自动取得改动范围和发布权限。

Review alone can keep finding work beyond the request. Judgment alone can stop before the result has been checked. Here, boundary decisions cannot silently erase verification obligations, and a review finding cannot automatically authorise wider changes or publication.

| 特色 / Feature | 实际作用 / Practical value | 实现位置 / Implementation |
|---|---|---|
| 两种技能各司其职 / Clear ownership | 把“该不该做”和“做得对不对”分开讨论 / Separate action choices from correctness evidence | [组合契约](references/composition.md) |
| 三种编排方式 / Three modes | 稳定任务串行，关键门联合重判，新证据出现时局部回退 / Serial execution, joint checkpoints or adaptive re-entry | [独立脚本](scripts/review_flow.py) |
| 内容与证据绑定 / Snapshot-bound evidence | 文件或适用规则变化后，旧验证和审查不再有效 / Content or owner changes invalidate old gates | SHA-256 snapshots and persisted events |
| Important 跨轮保留 / Persistent obligations | 换 reviewer 或提交空报告，不能让问题消失 / A new reviewer or empty report cannot erase an issue | Persistent issue ledger |
| 检查命令实际执行 / Executed verification | 留下命令、退出码、耗时、输出及哈希 / Retain argv, exit code, elapsed time, log and hash | Direct subprocess execution |
| 无云服务依赖 / Local operation | Python 标准库即可使用；agent 可由现有宿主提供 / Standard-library Python; use your existing agent host | Python 3.10+; no API key required |

这些是实现性质，不是审查效果的统计保证。脚本能拒绝缺失的证据，不能证明检查充分、风险判断准确，或 reviewer 真正拥有独立上下文。

These are implementation properties, not measured gains in defect detection. The runner checks evidence structure and freshness; it cannot prove that a test is adequate, a risk label is correct, or a reviewer was genuinely isolated.

## 先理解两个来源 / Understand the two inputs

**Judgment**：先区分确定流程与开放决策；给范围和投入设边界；失败先归因；评估委派成本；把不可继续的原因、证据和选项交出去。原版还引用了规划、上下文及计算资源等 owner 文档。组合版只在实际触发相应分支时要求这些文件可读，未触发的依赖不会阻断普通审查。

**Layered review**：收集意图、diff 和约定；先运行验证；评定风险；从正确性、安全、端到端行为和约定四个角度独立审查；复核候选问题；处理 Important，再报告结果与边界。Low/Medium/High、审批人数和三轮限制来自本地技能约定。

The original snapshots are preserved under [sources/](sources/). The combined entry point resolves two ambiguities explicitly: deterministic execution requires known steps, inputs **and** failure branches; missing owner documents matter only when their branch is invoked. See [sources and adaptations](references/sources.md) for the research record. The linked Anthropic material consists of engineering articles and product guidance; this suite does not present every local rule as an official paper or policy.

## 三种运行方式 / Three ways to run

| Mode | 顺序 / Sequence | 何时用 / When it fits |
|---|---|---|
| `serial` | 判断 → 验证 → 风险 → 独立审查 → 问题处置 → 完成 / Judge → check → risk → review → adjudicate → close | 边界稳定、检查明确 / Stable scope and known checks |
| `joint` | 同一顺序，审查前与完成前都增加判断检查点 / Same sequence, with judgment checkpoints before review and closure | 关键交接处需要重估工作是否仍合适 / Reconsider scope and sufficiency at critical gates |
| `adaptive` | 保留同一组硬门，允许带理由回到指定节点 / Same gates, explicit backward routes | 发现新证据、修复、失败归因或局部复核 / New evidence, repairs and local re-review |

`joint` 不会自动启动多个 agent；它规定判断和审查何时交换结论。独立审查可以由一个 worker 覆盖四个视角，也可由多个互不写入的 worker 分工。只有当分工收益大于交接、口径与合并成本时才并行。

The coordinator does not launch agents, call a model API or manage their permissions. The host supplies independent workers. A same-context self-check should be reported honestly, not relabelled as independence.

## 上手与安装 / Start and install

运行器无需安装依赖。解压后，在当前包目录执行；把 `python` 替换为你环境里的真实 Python 3.10+ 解释器。运行目录放到目标项目和分发包之外，避免把私人输出打进压缩包。

No dependency installation is needed for the runner. Work from the extracted package directory. Keep run state outside both the target project and the distributable tree.

```powershell
git clone https://github.com/Jxbbbbbyan/review-judgment-suite.git
cd review-judgment-suite
python -m unittest discover -s tests -v
python scripts/validate_package.py
```

也可下载 Releases 中的技能 ZIP 与 SHA-256 校验文件。Release 说明记录其来源提交；ZIP 包含逐文件清单，不含原始运行目录。Use the release ZIP and checksum file for a packaged install; the release notes identify the source commit, and the archive includes a per-file manifest.

```powershell
python scripts/review_flow.py --help
python scripts/review_flow.py --run-dir ../review-run init --project ../target-project --task "Review this change" --scope app.py tests/test_app.py --mode adaptive
python scripts/review_flow.py --run-dir ../review-run judge --decision proceed --execution agent --reason "The change is within the declared two-file scope"
python scripts/review_flow.py --run-dir ../review-run check --argv-json '["python", "-m", "unittest", "discover", "-s", "tests", "-v"]'
python scripts/review_flow.py --run-dir ../review-run risk --level low --reason "Internal change with no sensitive paths"
```

随后由独立 reviewer 产出带当前 snapshot 的 JSON，再通过 `review --input` 导入。存在 Important 时先修复或给出经复核的不修理由。完整的首次流程、联合检查点、回退、失败归因、人工决定和结果格式见 [workflow.md](references/workflow.md)。

For skill discovery, place this entire directory under the host's configured skill root and retain the folder name `review-judgment-suite`. For Codex, the conventional user location is `~/.codex/skills/review-judgment-suite`; for another host, use its supported skill directory. Copying files alone does not prove automatic invocation. The CLI works independently of discovery.

安装组合包时不需要覆盖原 `anthropic-review` 或 `judgment`。原技能继续保留；使用本组合时以本包的冲突处理契约为准。回滚只需移除组合包并保留运行证据，不涉及共享预设、认证或模型配置。

## 交付与可复查性 / Deliverables

```text
review-judgment-suite/
├── SKILL.md                         combined skill entry
├── README.md                        bilingual explanation and tests
├── agents/openai.yaml               discovery metadata
├── scripts/review_flow.py            local workflow coordinator
├── scripts/build_release.py         clean ZIP and file manifest
├── references/                      contracts, CLI and source mapping
├── sources/                         unchanged local skill snapshots
├── examples/                        redacted case and synthetic review task
└── tests/                           executable gate regression tests
```

运行证据保存在另选的 `run-dir`：`state.json` 与 `check-*.log`。报告应列明问题数量、风险、处置、真实检查结果、未覆盖事项和回滚方法。保留原始记录供授权人员核查；对外只分享经过检查的脱敏摘要。

This package does not merge, deploy, publish or submit to Grok Bot. Human approval records remain attestations supplied from actual authorisation; neither an AI name nor a successful exit code grants permission. A timeout contains the direct subprocess only, so use host-level containment for commands that create long-lived child processes.

<a id="tests"></a>
## 测试与独立智能体案例 / Tests and independent-agent cases

### 可执行回归 / Executable regression

```powershell
python -m unittest discover -s tests -v
```

覆盖三种模式、向前跳步拒绝、内容与约定变化后失效、陈旧报告、Important 跨轮保留、修复后的独立确认、人工证据数量与去重、失败归因、权限拒绝、超时、日志变更、路径越界、并发锁和预算耗尽。测试中模拟的 reviewer 与审批记录只用于验证门的行为，不冒充真实的独立审查或人工审批。

The regression suite tests state-machine properties, including negative cases. Synthetic reviewer and approval objects are test fixtures. They do not demonstrate independent reasoning, authenticated human approval or a real-world defect-detection rate.

### 打包前已经做过的工作流 / Workflow used before this package

[脱敏案例全文](examples/prior-independent-review.md)保留了此前一个技术文档任务的过程：主 agent 读取材料并修改；独立 reviewer 在新上下文核对 diff 和证据；主 agent 整合意见、跑检查并确认交付。该轮记录包括 162 项文档引用检查、4 段命令语法检查和五份模型文件的一致性核对。

The [redacted case](examples/prior-independent-review.md) describes an observed author/reviewer workflow from before this coordinator existed. It preserves what was checked and what was not: documentation and source consistency were verified; GPU execution was not repeated. It is not retroactive proof that the new CLI orchestrated the old run.

### 本次独立前向试用 / Independent forward trial

The fixture under [examples/forward-task/](examples/forward-task/) was used by a fresh reviewer exercising the packaged workflow. Actual outcomes and final command counts are recorded in [test-results.md](examples/test-results.md). Synthetic state-machine tests and live independent-agent observations are reported separately.

独立试用已从原始任务和代码出发完成，没有提供作者预设答案。23 项流程回归全部通过；另一个保留缺陷的样本产生两项 Important，流程正确拒绝完成。结果只说明这些输入上的表现；完整输出、修复与未覆盖部分见测试记录。
