# Authorship, reference and adaptations / 原创归属、参考与适配

**Judgment 由本项目作者 Jxbbbbbyan 原创，没有外部参考来源。审核方法参考 Anthropic 的一篇工程文章，并在本项目中再开发。** 两者各自的职责和实现机制分别说明如下。

**Judgment is original work by this project's author, Jxbbbbbyan, with no external reference source. The review method adapts one Anthropic engineering article.** Their responsibilities and the supporting implementation are identified separately below.

## Review reference / 审核参考

[How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/) — Addy Osmani, Morgan Westlee Lunt and Qing Wang; published 2026-10-15; checked 2026-11-02. This is a public engineering article describing the team's practice.

| 文章中的方法 / Article practice | 本流程的对应方式 / Workflow adaptation |
|---|---|
| 先运行可验证的检查，再由新上下文复核 / Executable verification followed by fresh-context review | 保存真实检查输出；由宿主提供独立 reviewer / Retain check output; the host supplies an independent reviewer |
| 候选问题复核、分类及逐项回应 / Verify, classify and answer findings | Important / Nit / Pre-existing 与带证据的问题处置 / Finding tags and evidence-backed dispositions |
| 按风险安排人工审批，AI 不能替代人 / Risk-scaled human approval | Low / Medium / High 与人工批准记录；身份认证由宿主负责 / Risk tiers and approval attestations; authentication remains with the host |
| 限制复审轮次、处理同类问题并避免重复报告 / Bound re-review and address bug classes without repeats | 最多三轮，并持续保留未解决的 Important / At most three rounds, with unresolved Important obligations retained |

## Original Judgment / 原创判断纪律

Judgment 负责判断是否行动、做到哪里、何时重规划或停止。原始内容包括确定流程与自主判断的取舍、判断/放弃/失控预算、失败归因、上下文保留优先级、委派成本，以及停止时如何交出证据与选项。这些内容归属于作者的原创设计，不归因于 Anthropic 或其他外部文章。

Judgment governs whether to act, how far to go, and when to replan or stop. Its original material covers deterministic execution versus agent decisions; decision, abandonment and scope budgets; failure attribution; context retention; delegation cost; and evidence-based handoff. These are the author's original designs, not material attributed to Anthropic or another external publication.

## Implementation and differences / 实现与适配差异

三种运行模式、Python 状态机、文件快照、跨轮问题台账和可选跨模型传递由本项目实现。Judgment 为 Review 设定边界与决策条件；Review 返回证据和待决事项。两者的关系见[流程契约](composition.md)。

This project implements the three modes, Python state machine, file snapshots, persistent finding ledger and optional cross-model transport. Judgment sets Review's boundaries and decision criteria; Review returns evidence and unresolved decisions. See the [workflow contract](composition.md).

- **轮次 / Rounds:** 文章在三轮复审后要求退一步重考虑；脚本还把内容变化和重新打开已有审查计入同一上限。The runner also counts content changes and reopened passes toward its three-round cap.
- **批准 / Approvals:** 文章描述可信作者名单和特定提交上的批准；脚本只保存当前快照的人工批准声明，不维护可信作者名单或认证批准者。The runner stores snapshot-bound attestations, without a trusted-author registry or identity authentication.
- **复核 / Finding verification:** 本流程要求候选问题复核，但未实现文章中的多组 agent 投票机制。Reviewer isolation and candidate verification are host responsibilities; the runner does not implement voting groups.
- **交付 / Delivery:** 文章还讨论合并队列、渐进发布、回滚与事故评估；本脚本只协调审查，不提供这些基础设施。Merge queues, staged releases, rollback and incident evaluation are outside this runner.

## Source records and redistribution / 源记录与分发

原始技能及 Judgment 的三份细则保留在 [sources/](../sources/)，内容未改；[manifest.json](../sources/manifest.json) 记录五份文件的校验值。快照用于核对来源与适配差异，不是运行依赖。涉及原预设中的领域规则时，只在该分支实际需要且规则可读时引用，不自行补造阈值。

The [source snapshots](../sources/) preserve the original skills and three Judgment references unchanged; [the manifest](../sources/manifest.json) records hashes for all five files. They support provenance checks and are not runtime dependencies. Domain-specific owner rules apply only where relevant and available.

外部文章仅通过链接引用，不随包复制。项目独立维护，不暗示 Anthropic 参与、赞助或背书；文章的权利归属与作者原创 Judgment 的归属分别保留。仓库公开本身不构成对全部内容的再许可，也没有替外部文章授予 MIT 许可。

The article is linked rather than bundled. This independently maintained project implies no Anthropic affiliation, sponsorship or endorsement. Attribution of the article remains separate from authorship of Judgment. Public availability is not a blanket redistribution licence, and no MIT licence is assigned to the external article.
