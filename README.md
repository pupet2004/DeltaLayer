# DeltaLayer

**Persist change, not context. Let the next model reconstruct the rest.**

面向长期 AI Agent 工作的极简项目连续层。保存有持续意义的项目变化，让下一任 Agent 按需读取历史，并用当前源码和测试核实现实。

**状态：Open Design Proposal + Experimental Prototype。** 不是成熟插件发布，也不是已经证明有效的通用 Agent Memory 方案。

[Apache-2.0](LICENSE) · [首发文章](ARTICLE.md) · [v0 设计规范](DESIGN.md) · [实验与边界](EXPERIMENTS.md) · [相关工作](PRIOR_ART.md)

## 三个文件

```text
your-project/
├── AGENTS.md                  # Agent 的读写行为约定
├── PROJECT.md                 # 可重建的当前项目视图
└── .deltalayer/
    └── changes.jsonl          # 只追加的语义变化历史
```

不记录“读了哪些文件、调用了哪些工具”，而是记录“项目从此有什么不同”：

```json
{"time":"2026-09-21T15:30:00+08:00","source":"agent","changes":["native runtime 新增严格工具参数校验，非法参数在进入 handler 前被拒绝"]}
```

这是格式示例，不是实验原始记录。没有持久变化时，`changes: []` 完全正常。

启动时先读 `PROJECT.md`，再读最近变化；不够就向前回溯，够了就开始工作。读取深度由模型判断，具体实现由源码、测试和实际工作区确认。完成有意义的变化后追加记录，必要时更新 `PROJECT.md`。

v0 不要求 embedding、向量数据库、独立总结 Agent 或确定性历史 reducer。它也不替代 Git、测试、权限控制或运行时 checkpoint。

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

## 试用原型

原型只用 Python 标准库。以下命令在本仓库根目录执行，初始化的是独立示例目录，不会修改实验材料：

```powershell
python prototype/deltalayer.py --root ./demo-project init
python prototype/deltalayer.py --root ./demo-project append --source human --change "确定以 append-only semantic changes 作为连续性实验入口"
python prototype/deltalayer.py --root ./demo-project recent --limit 3
python -m unittest discover -s prototype -p "test_*.py"
python tools/verify_release.py
```

`recent` 返回继续回溯所需的 `next_before`。原型不会调用模型，也不会自动从对话提取变化；`rebuild-context` 只打包上下文，不自动重建 `PROJECT.md`。`init` 会在目标项目的 `AGENTS.md` 追加约定。请先在示例目录试用；并发写入与崩溃恢复尚无生产级保证。更多命令见 [原型说明](prototype/README.md)。

## 我们想验证的问题

DeltaLayer 不声称发明了 agent continuity、append-only log 或 handoff。它尝试验证一个更窄的假设：

> **语义变化是否可以成为项目连续性的最小原语，并把历史解释交回给 LLM？**

最需要的反馈是已有相似实践、具体反例，以及与高质量 handoff 的公平对照。欢迎提供任务、历史输入、回溯行为、验证结果和未测指标，不必只报告成功。

许可、归属与公开范围见 [发布清单](RELEASE_CHECKLIST.md)。
