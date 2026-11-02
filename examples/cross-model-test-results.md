# Optional cross-model transport tests / 可选跨模型传输测试

Date: 2026-11-02. These tests exercise local message transport using synthetic hosts/models and a synthetic worker. They do not call a real model, install host clients or consume Grok Bot quota. Core review is tested separately from the actual model identity or quality, which this protocol does not authenticate.

本轮实现默认关闭的发送、文件网关、接收、worker 连接、返回与导入接口。Core `review_flow.py` 没有导入这个模块，也未增加原生客户端、API key 或会话恢复依赖。

## Executed checks / 实际检查

```powershell
python -m unittest discover -s tests -v
python scripts/validate_package.py
```

The initial **35-test run passed** (23 core + 12 transport tests). Independent security/end-to-end review then reproduced two issues: private runtime files under the optional tree could enter the ZIP, and a Chinese UTF-8 request could fail in the demo worker under a GBK text stream. Both were repaired and regression checks added. Additional tests exercise Codex → Grok Bot role routing and external Important findings blocking core closure.

Final observed regression output: **Ran 39 tests ... OK** (23 core + 16 optional transport/package tests); package validation checked **62 local links and 5 source snapshots, with no errors**. The self-review run records the actual command output before publication. Passing tests show gate behaviour for these inputs, not real cross-provider semantic review.

| Case / 场景 | Expected evidence / 核对结果 |
|---|---|
| DSH → Codex local round trip | Queued → gateway forward → worker response → poll → core import; no automatic close |
| Codex → Grok Bot role route | Correct declared target retained through return envelope; synthetic worker only |
| Disabled config or missing enable/share confirmation | No delivery or worker execution |
| Duplicate request/return/worker | Existing messages are not overwritten; no automatic worker retry |
| Bad route, request mutation or response mismatch | Refused before core import |
| Scoped content changed or wrong original run | Stale/misbound return refused |
| Timeout or failed worker | Permanent started receipt retained; retry requires manual reconciliation |
| External Important finding | Import succeeds as evidence; core close remains blocked |
| Legacy console encoding with Chinese input | Demo worker reads protocol bytes as UTF-8, independently of stdin locale |
| Private local config/mailbox under optional tree | Explicit static release allowlist excludes both, even if gitignored |

## Package review repairs / 打包审查修复

The release builder now enumerates four static optional assets rather than recursively including that directory. A test creates a private sentinel config and queued code payload inside an ignored mailbox; neither is selected for the archive. Source snapshots remain byte-identical to their recorded manifest.

发布包不包含本机网关地址、真实配置、用户会话、原始代码请求或审批材料。路由配置示例保持 disabled。合成 worker 返回的空发现只用于测试传输，不能当作实际独立审查结果。

## Self-review with this skill / 使用组合技能自审

The maintainer records scope, judgment, executed checks, risk and a fresh independent report in a private run directory outside the repository. Independent model identity and human approval are not fabricated. Publication authorisation comes from the user's explicit request, separately from the core runner's human-approval attestation gate. No Grok request is submitted as part of self-review.

这次自审使用实际检查输出和独立 reviewer 证据。人工批准记录不由 AI 伪造；核心中是否可以 close 与用户是否授权发布是两个分别记录的事实。原始自审状态和命令日志不进入公开包。
