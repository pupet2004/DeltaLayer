# DeltaLayer

**Persist change ownership, not context. Let the next model reconstruct the rest.**

面向长期 AI Agent 工作的极简项目连续层。保存有持续意义的项目变化，让下一任 Agent 按需读取历史，并用当前源码和测试核实现实。

**状态：Open Design Proposal + Experimental Prototype，当前设计版本为 v0.2.1 Conversation Delta ownership model。** 不是成熟插件发布，也不是已经证明有效的通用 Agent Memory 方案。

[Apache-2.0](LICENSE) · [首发文章](ARTICLE.md) · [v0.2.1 设计规范](DESIGN.md) · [实验与边界](EXPERIMENTS.md) · [相关工作](PRIOR_ART.md)

## 两层历史

```text
your-project/
├── AGENTS.md                  # Agent 的读写行为约定
├── PROJECT.md                 # 可重建的当前项目视图
└── .deltalayer/
    ├── changes/               # owned / historical Conversation Delta 文件
    │   ├── <conversation>.json
    │   └── <conversation>.frozen.json  # optional archival name
    └── changes.jsonl          # legacy v0 history，只读兼容
```

新的核心单位是一个真实 conversation 的 Delta：

```json
{
  "started_at": "2026-09-21T22:00:00+08:00",
  "updated_at": "2026-09-21T23:15:00+08:00",
  "source": "codex",
  "changes": ["native runtime 新增严格工具参数校验"]
}
```

它是一个由单个 conversation 所拥有的项目语义变化记录。当前 conversation
可以更新、改写或删除自己 Delta 中的净变化；另一个 conversation 不得接管
它。即使没有持久变化，也必须保存 `changes: []` 的 Delta。

**A conversation owns exactly one Delta during its lifetime.**

新 conversation 永远 `start` 新文件；Within the same conversation context,
tasks continue using the same owned Delta path，不从目录中的旧文件推断归属。
handoff 是给未来 Agent 的交接提示，
不是 Delta 生命周期事件；不要求 `freeze`。当前 prototype 仍保留 `freeze`
作为可选归档命令，旧 `.frozen.json` 仍可读。不需要全局 `.current` 或真实
产品 conversation ID。

一个好的 change 不只说“发生了什么”，还尽量说明为什么未来 conversation
需要知道它来作出、核验或避免某个项目决策。这是 change 文本的一部分，不是
额外的 `reason`、`impact` 或其他结构化字段；它仍然只是最小语义差异。

启动时先读 `PROJECT.md`，再读最近 Conversation Deltas；不够就向前回溯，最后才进入 legacy `changes.jsonl`。读取深度由模型判断，具体实现由源码、测试和实际工作区确认。

DeltaLayer v0.2.1 不要求 embedding、向量数据库、独立总结 Agent、确定性历史 reducer 或数据库。它也不替代 Git、测试、权限控制或运行时 checkpoint。此前 v0 dogfood 使用 shared append-only JSONL；Workbench 和 Qicetai evidence 保留其真实旧模型边界。

## 已观察到什么

一个真实长期项目中的 48 个成功任务被**事后回填**成 Delta，并非 48 次在线自动写入。公开版本见 [`experiments/public-deltas.jsonl`](experiments/public-deltas.jsonl)，已匿名化并做语义脱敏：

| 同组材料 | 字符数 |
| --- | ---: |
| Task 最终消息 | 40,555 |
| 紧凑 Delta JSON，含 metadata | 10,398 |
| 纯 `changes` 文本 | 4,585 |

纯变化文本约为最终消息字符数的 **11.3%**。这不是完整 Session 压缩比，更不是总任务 token 节省。

读取行为出现过 `3 → 8 → stop` 和 `3 → stop`。在 H5 开放式续接中，C 读取 8 条 Delta 后，结合源码、Git 和测试完成真实开发任务。

**H5 = `PARTIALLY_SUPPORTED`。** 支持“少量变化可作为项目理解入口”；尚未证明显著减少总源码考古或总 token，也未证明优于高质量 handoff。A/B 对照组同样完成任务。早期理解实验还出现过把“未启动”误读成“下一步”的失败。

实验方法、公开记录和缺失材料见 [EXPERIMENTS.md](EXPERIMENTS.md)。原始 Session、完整源码、真实 fixture、凭据和业务数据不在仓库中。

## 试用 v0.2 原型

原型只用 Python 标准库。以下命令在本仓库根目录执行，初始化的是独立示例目录，不会修改实验材料：

```powershell
python prototype/deltalayer.py --root ./demo-project init
python prototype/deltalayer.py --root ./demo-project start --source human
# 将 start 输出的 _path 传给后续命令
python prototype/deltalayer.py --root ./demo-project update --conversation <delta-path> --change "确定以 Conversation Delta 作为连续性入口"
python prototype/deltalayer.py --root ./demo-project current --conversation <delta-path>
python prototype/deltalayer.py --root ./demo-project recent --limit 3
python -m unittest discover -s prototype -p "test_*.py"
python tools/verify_release.py
```

`recent` 返回继续回溯所需的 `next_before`；`older` 可以跨 Conversation Delta 文件回溯到 legacy JSONL。当前 prototype 仍提供 `freeze` 作为可选归档操作，但它不是 v0.2.1 handoff 要求。原型不会调用模型，也不会自动从对话提取变化；`rebuild-context` 只打包上下文，不自动重建 `PROJECT.md`。`init` 会创建 `.deltalayer/changes/`，并在目标项目的 `AGENTS.md` 追加 conversation 约定。请先在示例目录试用；并发写入与崩溃恢复尚无生产级保证。更多命令见 [原型说明](prototype/README.md)。

## 我们想验证的问题

DeltaLayer 不声称发明了 agent continuity、append-only log 或 handoff。它尝试验证一个更窄的假设：

> **语义变化是否可以成为项目连续性的最小原语，并把历史解释交回给 LLM？**

最需要的反馈是已有相似实践、具体反例，以及与高质量 handoff 的公平对照。欢迎提供任务、历史输入、回溯行为、验证结果和未测指标，不必只报告成功。

许可、归属与公开范围见 [发布清单](RELEASE_CHECKLIST.md)。
