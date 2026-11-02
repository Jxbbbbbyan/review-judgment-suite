# Code review and agent workflow — use-case map / 用途与技术路线

[README](../README.md) · [CLI](workflow.md) · [Tests](../examples/test-results.md)

The suite combines **judgment** and the locally named **anthropic-review** skill. It is an independent project informed by linked public engineering articles, without Anthropic affiliation or endorsement. Keywords describe the implemented workflow, not an official product integration.

## Match a request / 从需求定位

| Request / 需求 | Technical route / 技术路线 | Fit and boundary / 适用范围 |
|---|---|---|
| Evidence-led AI code review / 有证据的代码审查 | Explicit checks → risk → four review perspectives → adjudication | Hosts supply actual reviewer contexts; JSON alone cannot create independence |
| Agent guardrails and scope control / 代理边界控制 | Judgment checkpoints, declared file scope and bounded re-entry | Process gates, not an execution sandbox |
| Review orchestration and human-in-the-loop / 审查编排与人工决定 | serial / joint / adaptive workflows, approval attestations | Records real external decisions; does not authenticate identities |
| Stale tests after a code change / 代码变更后证据过期 | SHA-256 content and convention snapshots | Only declared files and included owner documents are tracked |
| Lost findings across review rounds / 多轮复核丢问题 | Run-wide finding IDs and persistent Important ledger | A repair needs a new snapshot and current independent confirmation |
| Tool failures and uncontrolled retries / 失败后反复重试 | Recorded failure classification, one parameter correction, stop/handoff | Semantic attribution remains an agent/human responsibility |

中文常用表达：判断与审查组合技能、独立智能体审查、代码审查状态机、证据过期检测、问题闭环、可恢复审查流程、失败归因、人工审批记录。相关实现和限制均可从表中的路线回到[主脚本](../scripts/review_flow.py)及[契约](composition.md)。

## Inspect before adopting / 使用前核对

1. Read [the skill](../SKILL.md) and [source mapping](sources.md).
2. Run the [regression suite](../tests/test_review_flow.py) and local package checks.
3. Choose a bounded task and suitable check commands. The Python standard library is sufficient; your agent host is separate.
4. Examine [the independent forward trial](../examples/test-results.md): it includes a deliberately broken fixture whose completion was refused, with limitations stated.

## Query examples / 查询表达示例

```text
"code review" "failure attribution"
topic:code-review topic:agent-skills
"persistent Important" in:readme
"独立" "审查" in:readme
```

These illustrate the project vocabulary. They are not promises of rank, indexing time or recommendation frequency. GitHub repository search uses name, description and topics by default; README content participates with `in:readme`. [Search documentation](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories).
