# Sources and adaptations / 来源与改写

Research checked on 2026-11-02. These are **engineering articles and product documentation**, not evidence that every rule below is an Anthropic paper or official company policy. This is an independent integration of two local skills. No Anthropic affiliation, sponsorship or endorsement is implied.

| Primary source / 原始资料 | Used for / 采用内容 | What is ours / 本项目自行规定 |
|---|---|---|
| [Building effective agents](https://www.anthropic.com/research/building-effective-agents), 2024-12-19 | Distinguish predetermined workflows from agent decisions; use simple composable paths and programmatic gates | Three-way mode contract and CLI state graph |
| [How we built our multi-agent research system](https://www.anthropic.com/research/multi-agent-research-system), 2025-06-13 | Separate contexts and scoped workers; account for coordination cost and artifact handoff | Four review perspectives, JSON report contracts and carried issues |
| [Effective context engineering for AI agents](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents), 2025-09-29 | Curate context and externalise useful state for long tasks | Scope hashes, event ledger and owner-file invalidation |
| [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices), living documentation | Verifiable tasks, review and host-enforced checks | Low/Medium/High thresholds, human counts and three-round limit are local conventions, not quoted official standards |

The original `anthropic-review` snapshot names a Claude-team layered workflow but supplies no bibliography. The suite does **not** retroactively assert that all its particulars were published by Anthropic. The judgment creation notes referenced secondary translations and third-party failure-handling articles; this integration uses the primary materials above for architectural motivation, and treats the original failure rules as local policy.

原技能快照位于 `sources/`，内容未改，校验值写在 `sources/manifest.json`。组合入口和三个工作模式是本次新增实现。源快照用于溯源，不要求安装旧预设，也不会被自动执行。

## Attribution and redistribution / 署名与分发

Official articles remain linked, not bundled or reproduced. Local skill snapshots were supplied from the maintainer's environment; no third-party ownership or licence grant is inferred. This distribution does not assign an MIT licence to the original skills or Anthropic material. Source availability is not a blanket redistribution licence. Original project code/documents and snapshots are identified separately in the manifest.
