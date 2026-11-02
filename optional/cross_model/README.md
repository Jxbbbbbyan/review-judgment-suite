# Optional cross-model review transport / 可选跨模型审查传输

This directory contains the sender, file gateway, receiver, return path and configured worker interface. It is never imported by the core and has no model SDK dependency. The example config is disabled; explicit configuration and command-line opt-in are required before delivery.

这里是独立可选层。一个模型开发，另一个模型审核；请求携带选定材料、内容快照和回传关联，结果仍通过原来的核心审查门。实际模型运行由已有宿主负责。

| File | Purpose / 用途 |
|---|---|
| [review_bus.py](review_bus.py) | create / send / gateway / take / work / respond / poll / import |
| [routes.example.json](routes.example.json) | Disabled routing examples for DSH → Codex and Codex ↔ Grok Bot |
| [demo_worker.py](demo_worker.py) | Synthetic transport fixture; no model call or substantive review |

[完整双语接入手册 / Full setup and protocol](../../references/cross-model-review.md)

```powershell
python optional/cross_model/review_bus.py --help
```

Use Python 3.10+ and the standard library. Native host clients, remote gateways, credentials and host-specific wrappers remain optional and separately configured. Installing the directory does not scan sessions, make paid requests or resume a conversation.
