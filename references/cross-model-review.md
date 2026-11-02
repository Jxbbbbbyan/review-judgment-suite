# 可选：跨模型开发与审核 / Optional cross-model review

让一个模型负责开发，另一个模型在独立上下文复核，再把发现送回原任务。这个可选层可以在 DeepSeek Harness、Codex 与 Grok Bot 等宿主角色之间传递请求和报告；你也可以继续只使用核心流程，直接导入独立报告。

Use one model to develop and another to review in a separate context, then return the findings to the original task. This optional layer carries requests and reports between host roles such as DeepSeek Harness, Codex and Grok Bot. Core-only review remains available without it.

## 交付范围 / What is included

| Part / 部分 | Interface / 接口 | Default / 默认 |
|---|---|---|
| Sender / 发送端 | `create` selects context; `send` queues the request | No session or credential scanning |
| Gateway / 网关 | `gateway` forwards configured file-mailbox routes | No listening port, daemon or remote endpoint |
| Receiver / 接收端 | `take` exports the delivered request | No automatic model call |
| Worker connection / 内部连接 | `work` supplies JSON on stdin and expects report JSON on stdout | No worker command configured |
| Return / 返回端 | `respond` publishes a report; `poll` fetches it | No session resume or callback execution |
| Core import / 核心导入 | `import` correlates the return and uses the existing core gate | No automatic closure, approval or repair |

All transport code is under [optional/cross_model/](../optional/cross_model/README.md), using Python 3.10+ standard library only. The core never imports it. Actual host clients, model runtimes and private gateways remain separately supplied optional integrations. Installing the suite does not install or activate those clients.

发送、接收、文件网关、返回与 worker 连接代码全部集中在可选目录。它们不成为核心技能的运行条件。此处交付通用传输契约，不宣称三个产品的原生客户端或任意私有网关已经即插即用。

## 路由示例 / Route examples

```text
DeepSeek Harness / developer model A
  → sender → request mailbox → file gateway
  → Codex / reviewer model B
  → report mailbox → receiver → original review gate

Codex / developer model B
  → sender → request mailbox → file gateway
  → Grok Bot / reviewer model C
  → report mailbox → receiver → original review gate
```

Configure the model actually used at each end. Equal declared model labels are rejected, but labels cannot prove model identity or independent context. Different hosts may run the same model. A request carries intent, diff and conventions, not the author's preferred conclusion.

如果原有服务采用不同协议，接入端需要转换输入输出。只返回“请求已提交”的脚本不是已完成审核的 worker；异步服务可以用 `take` / `respond` 分开收发，不必伪造同步结果。

## 依赖与启用 / Dependencies and opt-in

| Usage / 用法 | Needed / 需要 |
|---|---|
| Core-only / 仅核心 | Python and your current reviewer host; no spool or Grok connection |
| Manual cross-host / 人工跨宿主交接 | This optional module, private mailbox and compatible report JSON |
| Configured worker / 自动 worker | A trusted argv wrapper for the actual host and its own optional client dependencies |
| Private remote gateway / 私有远程网关 | Your gateway/client, credentials and protocol adapter; none are copied into this repository |

Copy [routes.example.json](../optional/cross_model/routes.example.json) outside the repository, set a private `spool_root`, choose the routes and change `enabled` to true. Transport commands also require `--enable`; `send` additionally requires `--confirm-share`. Disabled routing creates no mailbox and starts no worker.

文件网关依赖操作系统目录权限，不提供身份认证、加密或互联网多租户服务。摘要用于检测错配和误改，不能防止有目录写权限的人同时改消息与摘要。保留运行文件用于核对，不自动清理。

## 完整走一条请求 / Walk through one request

First initialise the core run, judge scope, execute meaningful checks and record risk using [workflow.md](workflow.md). In joint mode, complete its review judgment checkpoint. Requests cannot be prepared for a closed or stale core run.

准备仅含所需材料的 `context.json`，由使用者选择并脱敏：

```json
{
  "intent": "Review the parser change against its stated contract",
  "diff": "Selected, inspected diff",
  "conventions": "Applicable review conventions, or an explicit statement that none apply"
}
```

The sender does not collect the whole repository, private sessions or thread IDs. Review the selected text before sharing. Scope and snapshot travel with the request; a run-binding digest correlates it to the original core run without a plaintext project-path field.

### 1. 准备与发送 / Prepare and send

```powershell
python optional/cross_model/review_bus.py create --run-dir ../review-run --context ../context.json --source-host dsh --source-model developer-model-A --target-host codex --target-model reviewer-model-B --output ../request.json
python optional/cross_model/review_bus.py send --config ../routes.local.json --request ../request.json --enable --confirm-share
```

`create` only writes your selected request. `send` queues it in `requests/<target>/<id>.json` and returns `completed: false`. Its acknowledgement does not mean a model reviewed anything. All paths are examples; keep context, requests, config and responses outside the repository.

### 2. 中转与接收 / Forward and receive

Replace `UUID_FROM_CREATE` with the printed request ID:

```powershell
python optional/cross_model/review_bus.py gateway --config ../routes.local.json --target codex --request-id UUID_FROM_CREATE --enable
python optional/cross_model/review_bus.py take --config ../routes.local.json --target codex --request-id UUID_FROM_CREATE --output ../reviewer-request.json --enable
```

Both sides use the same private filesystem location or controlled shared mount. The file gateway validates the route, digest and target before forwarding. It does not deploy a network gateway. Pass the received material to a fresh context on your actual reviewer host.

### 3. 返回与导入 / Return and import

Ask the reviewer to produce the [core review JSON](workflow.md) with the request's exact snapshot. Findings must be verified against source evidence; covered perspectives and reviewer independence must reflect the actual host execution.

```powershell
python optional/cross_model/review_bus.py respond --config ../routes.local.json --request ../reviewer-request.json --report ../review.json --enable
python optional/cross_model/review_bus.py poll --config ../routes.local.json --request ../request.json --output ../response.json --enable
python optional/cross_model/review_bus.py import --request ../request.json --response ../response.json --run-dir ../review-run --enable
```

导入会核对请求 ID、请求摘要、返回目标、内容快照和原 run 绑定。内容已变、错误请求、错误目标或重复 reviewer 都会被拒绝。成功导入只增加证据；Important、人工决定和完成条件仍由核心门处理。

For Codex → Grok Bot, use source `codex`, target `grok-bot`, their actual declared models and that target in the receive/worker commands. No real paid request is needed to test message transport.

## 可选 worker / Optional worker connection

Instead of `take` / `respond`, configure `workers.<target>` with the actual declared model, an explicit working directory and trusted argv:

```json
{
  "model": "reviewer-model-B",
  "cwd": "directory-containing-your-adapter",
  "argv": ["python", "your_host_adapter.py"]
}
```

```powershell
python optional/cross_model/review_bus.py work --config ../routes.local.json --target codex --request-id UUID_FROM_CREATE --timeout 120 --enable
```

The wrapper receives **UTF-8 request JSON on stdin**, invokes an authorised independent reviewer, waits for the actual result and emits **one UTF-8 report JSON on stdout**. Diagnostics go to stderr. Relative config paths resolve from the config directory. Commands come from trusted local configuration, never from the request. Credentials stay with the host; no sandbox or permission elevation is supplied.

附带的 [demo_worker.py](../optional/cross_model/demo_worker.py) 只验证传输，不调用模型；不能拿它的空发现报告代替真实审核。DSH、Codex、Grok Bot 的原生客户端、OAuth、私有 HTTP 网关和会话恢复脚本均是外部可选接入，不会被这个目录自动安装或调用。

Workers retain a permanent started receipt before execution. Timeout or failure does not automatically resend a possibly paid request. Inspect the host and outcome before manual recovery; timeout only contains the direct subprocess, not remote jobs or descendants. Do not reroute a denied request to bypass its restriction.

## 测试与边界 / Tests and limits

Duplicate delivery does not overwrite mailboxes. Oversized or duplicate-key JSON, altered digests, invalid paths, stale snapshots and mismatched responses are refused. Model labels and `independent: true` remain declarations, not authenticated evidence of real model execution.

[测试记录](../examples/cross-model-test-results.md) separates local end-to-end transport from real model review. Synthetic workers cover DSH → Codex and Codex → Grok Bot role labels without calling either model provider. No live Grok request was sent. Raw messages, private URLs, tokens and session records do not belong in source control or a Release.
