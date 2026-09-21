# DeltaLayer v0.2 Prototype

发布包中的标准库原型。它模拟 conversation-granularity Delta，不假装知道真实 ChatGPT/Codex conversation ID。

## 试用

Python 3.10+。以下命令从 **DeltaLayer 仓库根目录** 执行，无需第三方依赖：

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python prototype/deltalayer.py --root ./demo-project init
$delta = python prototype/deltalayer.py --root ./demo-project start --source human | ConvertFrom-Json
python prototype/deltalayer.py --root ./demo-project update --conversation $delta._path --change "选择 Conversation Delta 作为连续性入口"
python prototype/deltalayer.py --root ./demo-project current --conversation $delta._path
python prototype/deltalayer.py --root ./demo-project freeze --conversation $delta._path
python prototype/deltalayer.py --root ./demo-project recent --limit 3
python prototype/deltalayer.py --root ./demo-project rebuild-context --limit 3
python -m unittest discover -s prototype -p "test_*.py" -v
```

`start` 总是创建一个新 Delta 文件，省略 `--change` 时也会持久化 `changes: []`。`update` 用重复的 `--change` 替换当前 active Delta 的净变化；不传 `--change` 会将当前 Delta 更新为空。`freeze` 将文件改名为 `.frozen.json`，之后不能 update。

## 文件结构

```text
.deltalayer/
├── changes.jsonl          # legacy v0 history, read-only
└── changes/
    ├── <conversation>.json
    └── <conversation>.frozen.json
```

Conversation Delta 的 schema：

```json
{
  "started_at": "2026-09-21T22:00:00+08:00",
  "updated_at": "2026-09-21T23:15:00+08:00",
  "source": "codex",
  "conversation_id": "optional",
  "changes": ["durable semantic difference"]
}
```

`conversation_id` 只有运行环境天然提供时才传入。原型通过显式 Delta path 让用户选择当前 conversation；它不制造或推断产品层 ID。

Conversation ownership comes from the current conversation's own remembered Delta path, never from discovering an existing active file.

新 conversation 永远调用 `start`，将返回的 `_path` 记在本对话上下文；同一对话连续多个任务也只更新该路径。旧的未 frozen `.json` 仍是可读的 unfinished / active-at-last-write history，不能被新对话接管、更新或代为冻结。不创建全局 `.current` 指针。

`current` 只是显式路径的读取命令，不是自动寻找“我的文件”。CLI 不验证真实产品身份，知道旧 active 路径的调用者技术上仍能传给 `update`；ownership 是 Agent 协议，不是访问控制保证。`freeze` 保持显式，只在最终 conversation handoff 调用，不在每次任务回复自动执行。不添加 lifecycle manager 或 hook。

## 读取与分页

`recent` 先读取 `.deltalayer/changes/*.json`，按 `updated_at`、`started_at` 和文件名稳定排序，再 fallback 到 legacy JSONL。空 Delta 会出现在历史读取中，但 `rebuild-context` 会把它放入 `empty_conversations`，不把空数组当成语义变化。

```powershell
$page = python prototype/deltalayer.py --root ./demo-project recent --limit 3 | ConvertFrom-Json
if ($page.next_before) {
    python prototype/deltalayer.py --root ./demo-project older --before $page.next_before --limit 3
}
```

Conversation cursor 使用文件名；legacy cursor 继续接受旧的 ISO time / line 形式。`older` 可以从 Conversation Delta 文件跨页进入 legacy history。旧 `changes.jsonl` 只读，不会因为新模型而迁移或重写。

## 时间与写入边界

`started_at` 与 `updated_at` SHOULD use an offset-aware ISO 8601 timestamp whenever available。不要为了新规则补造旧时刻或时区。reader 仍接受 date-only，并保留原始精度；单一 JSONL 的物理 append order 是该文件内部事件顺序，不按 timestamp 重排。

active Delta 更新使用同目录临时文件加原子替换；新文件使用 collision-safe 文件名。原型没有数据库、lock service、RAG、reducer 或自动摘要服务。

## 边界

- 原型不会调用模型或自动从对话提取 changes。
- `PROJECT.md` 是可重建 current view，不是历史权威。
- source、tests、Git 和实际 workspace 仍负责验证当前现实。
- malformed Conversation Delta 或 legacy 行会被单独 warning 并跳过，不会摧毁其他历史。
- 读取会扫描本地历史，没有大规模性能保证。
- 这是文件级 single-writer 原型，不提供多进程协调、崩溃恢复或防篡改保证。

当前测试覆盖 conversation lifecycle（包括中断后新对话不接管旧 active）、legacy fallback、混合时间精度、冻结、空 Delta、损坏文件、collision、CLI 和 2,500 个 Conversation Delta 分页场景。
