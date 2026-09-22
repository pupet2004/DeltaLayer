# DeltaLayer v0.2.1 Conversation Delta 设计规范

## 1. 定位

DeltaLayer 是一个面向长期 LLM / Agent 工作的轻量项目连续层。

它不保存完整对话，也不构建复杂的长期记忆系统。它保存的是：

> **一个由单个 conversation 所拥有的项目语义变化记录。**

核心思想仍然是：

> **Persist change ownership, not context. Let the next model reconstruct the rest.**

### 版本边界

此前的 v0 dogfood 使用一个共享的 append-only `.deltalayer/changes.jsonl`，每个 durable event 追加一行。

v0.2 将 append-only 的边界提升到 conversation level。v0.2.1
进一步收紧核心定义：

> **A Conversation Delta is a semantic change record owned by one conversation.**

一个 conversation 在其 lifetime 内恰好拥有一个 Delta。它可以修订自己的
净变化；另一个 conversation 不得因为发现某个文件而接管它。Delta 何时
不再被当前 conversation 使用，是外部事实，不是 Delta 自己的存储状态。

旧的 `changes.jsonl` 仍然是 legacy history，只读兼容，不迁移、不重写。Workbench Case 1 和 Qicetai Case 2 记录的是此前 shared-JSONL 模型的真实使用，不能伪装成当时已经使用 Conversation Delta 文件。

## 2. 核心持久化对象

```text
project/
├── AGENTS.md
├── PROJECT.md
└── .deltalayer/
    ├── changes.jsonl              # legacy v0 history, read-only
    └── changes/
        ├── <conversation-delta>.json
        └── <conversation-delta>.frozen.json  # optional archival name
```

语义分别是：

```text
PROJECT.md
= rebuildable current project view

.deltalayer/changes/*.json
= owned and historical Conversation Delta records

.deltalayer/changes.jsonl
= previous v0 history; read-only compatibility

source / tests / Git / workspace
= authoritative present reality
```

`.frozen.json` 是当前 prototype 保留的可选归档文件名。它不是 Delta
schema 的 status，也不是 v0.2.1 所要求的生命周期转换。已有
`.frozen.json` 文件继续作为历史读取；新的 handoff 不必须执行 rename。

## 3. Conversation Delta 定义

> **A Conversation Delta is a semantic change record owned by one conversation.**

这里的 conversation 是一次真实 Agent/chat conversation，不是开发任务：

- 一个 conversation 在其 lifetime 内恰好拥有一个 Delta；
- 同一个对话中完成多个任务，仍然只维护这个 Delta；
- 用户新开对话，就创建新的 Delta；
- 一个对话没有 durable semantic change，也仍然保存自己的空 Delta。

Conversation Delta 不是：

- execution transcript；
- task report；
- tool log；
- every intermediate event；
- every attempted solution。

它回答：

> **What became durably different during this conversation?**

## 4. 最小 schema

```json
{
  "started_at": "2026-09-21T22:00:00+08:00",
  "updated_at": "2026-09-21T23:15:00+08:00",
  "source": "codex",
  "conversation_id": "optional",
  "changes": [
    "修复 coarse timestamp reader，并保留单文件 append order"
  ]
}
```

字段约定：

- `started_at`：conversation 开始时间；
- `updated_at`：该 Delta 最近一次维护时间；
- `source`：例如 `codex`、`claude`、`human`、`ci-agent`；
- `conversation_id`：运行环境天然提供时可写入；不要求人为制造全局 ID；
- `changes`：一组从 conversation start 到当前的净持久语义变化。

不添加 `status`、`superseded_by`、`priority`、reducer metadata、sequence id、Lamport clock 或数据库字段。

## 5. Ownership 与 handoff

### Conversation ownership

> **A conversation owns exactly one Delta during its lifetime.**

当前 conversation 可以：

- update 自己的 Delta；
- rewrite 自己的 `changes[]`；
- remove 已被同一 conversation 撤销或取代的 change item。

另一个 conversation 不能因为发现一个旧文件而接管它。ownership 来自当前
conversation 自己记住的 Delta path，不来自目录发现、最新时间或全局指针。

`owned -> historical` 是对使用关系的描述，不是写入 Delta 的状态机：

- Delta 不需要 `status: active`；
- conversation 仍在使用自己记住的 path 时，它就是自己的 Delta；
- conversation 不再使用它之后，该文件自然成为历史记录；
- 新 conversation 永远创建自己的 Delta。

### Handoff

Handoff 是给未来 Agent 的交接提示，不是 Delta 生命周期事件。当前对话交还
控制权前应：

1. 更新自己 Delta 的最终净变化；
2. 必要时告诉用户下一任 Agent 应先读取这个 Delta；
3. 不要求 `freeze()`，也不把普通任务回复等同于 handoff。

当前 prototype 仍可通过 `freeze` 将文件改名为 `.frozen.json`，作为显式
归档操作；这不是 v0.2.1 协议的必需步骤。旧的未归档 `.json` 可能来自
异常中断、关闭窗口、崩溃或仍被原 conversation 使用。它仍可读取已有
durable changes，但新 conversation 不得接管或更新它。

## 6. 空 Conversation Delta

每一个 conversation 都必须有一个 Delta 文件，即使没有 durable change：

```json
{
  "started_at": "2026-09-21T22:00:00+08:00",
  "updated_at": "2026-09-21T22:00:00+08:00",
  "source": "codex",
  "changes": []
}
```

它表示：

> **This conversation existed but produced no durable semantic project change.**

空 Delta 用于记录 conversation existence boundary，而不是保存语义内容。
读取 continuity 时可以跳过它的 semantic content，但不得删除文件。原型的
`recent` 会保留它作为历史项；`rebuild-context` 将它放入
`empty_conversations`，不把空数组当成语义变化。

## 7. Change Writing Discipline

A Conversation Delta should be much smaller than the conversation that produced it。

通常推荐 1–4 个 concise semantic changes，但这不是硬性 schema 限制。每个 item 至少回答一个问题：

- What is now materially different?
- What important belief or assumption changed?
- What project decision or boundary changed?

不要记录：

- files read；
- commands run；
- ordinary test execution detail；
- step-by-step debugging；
- temporary attempts；
- failed approaches with no lasting consequence；
- unchanged facts；
- full validation reports；
- ordinary TODO lists；
- 已经由 `PROJECT.md` 充分表达的背景。

只有在验证建立了新的重要 project baseline 时，验证结果才值得进入 Delta。

强过滤器：

> **If a future agent could omit this sentence without materially changing its understanding or next decision, do not record it.**

`changes` 保存 semantic difference，不是 evidence package。测试报告、原始 session 和 provenance 应保存在适当的实验材料中，而不是塞进每个 Delta。

## 8. 新 conversation 的读取逻辑

新 conversation 启动时：

1. Read `PROJECT.md`；
2. Read 最近的 `.deltalayer/changes/*.json` Conversation Deltas；
3. 信息不足时，按最近优先继续读取更旧的 Conversation Deltas；
4. 仍不足时，继续读取 legacy `.deltalayer/changes.jsonl`；
5. Agent 判断已经足够后停止回溯；
6. 用 source、tests、Git 和 workspace 核验当前现实；
7. 新 conversation 永远创建自己的 Delta，将路径记在当前对话中；后续任务复用该路径，绝不接管发现的旧文件。

不因为目录里有 1,000 个 Delta 就全部读取。历史可以无限增长，context read depth 仍由模型判断并保持有界。空 Delta 可以快速跳过 semantic content，但文件仍然存在于历史。

## 9. 文件名、顺序与时间

新文件名使用 `started_at + source + collision-safe suffix`。原型会把不适合作为文件名的字符转换为安全形式，并在同一时间和 source 冲突时追加数字后缀。

`started_at` 与 `updated_at` 应尽量使用 offset-aware ISO 8601 timestamp：

> `time` SHOULD use an offset-aware ISO 8601 timestamp whenever available.

不要因为指导变更而补写旧时间、补造时区或修改旧 evidence。

Conversation history 的顺序必须稳定且可确定。原型按 `updated_at`、`started_at` 和文件名读取最近 Conversation Deltas；单个 legacy JSONL 内仍按物理 append order 读取。timestamp 是元数据，不是跨来源 authority，不引入分布式排序协议。

Conversation cursor 使用文件名；legacy cursor 继续兼容旧的 time/line cursor。分页使用已有的 `older` 机制，必要时从 Conversation Delta history 继续落入 legacy history。

## 10. 并行 conversation

不同 conversation 各自拥有文件：

```text
Agent A -> A's owned/historical Conversation Delta
Agent B -> B's owned/historical Conversation Delta
```

它们不需要争用同一个 `changes.jsonl` writer。v0.2 不设计 merge engine、authority resolver 或并发治理系统。若后续真实 dogfood 暴露复杂并行冲突，再单独处理。

## 11. PROJECT.md

`PROJECT.md` 仍然是 mutable / rebuildable current view，不是历史本身。

当新事实使它过期时：

- revise/remove stale current-state claims；
- current view 不能承担历史保存责任；
- 历史位于不再被当前 conversation 使用的 Conversation Deltas 和 legacy history 中；
- source、tests、Git 和 workspace 仍是 present implementation 的权威。

这一维护原则没有因为 v0.2.1 改变。

## 12. Legacy compatibility

`.deltalayer/changes.jsonl` 是 v0 history：

- 新 reader 必须支持它；
- 读取顺序上，新的 Conversation Deltas 先读，必要时再进入 legacy；
- legacy 文件只读，不因迁移而追加、重排、重写或转换；
- 不迁移 Workbench/Qicetai 的真实历史来让目录看起来整齐；
- 旧 evidence 必须保持字节不变。

旧 history 中存在 date-only 或其他低精度时间时，reader 应保留可读性；不得为读取而伪造具体时刻。单一文件的物理 append order 可以作为该文件内部事件顺序，但不能冒充跨来源全局时钟。

## 13. Prototype CLI

概念上的最小 conversation-oriented 操作是：

```text
init
start
update
show
current
recent
older
rebuild-context
```

当前 prototype 还保留 `freeze` 命令，用于兼容已有 v0.2 文件布局和可选
归档；它不是 v0.2.1 handoff 的必需操作。

典型流程：

```powershell
$delta = python prototype/deltalayer.py --root ./demo-project `
  start --source codex | ConvertFrom-Json

python prototype/deltalayer.py --root ./demo-project `
  update --conversation $delta._path `
  --change "完成一个持久语义变化"

```

CLI 无法天然知道真实 ChatGPT/Codex conversation ID，因此通过显式 Delta path 模拟 conversation ownership。它不假装拥有产品层 session identity。

`update` 会原子覆盖当前 conversation 自己的文件；`start` 永远创建新文件，
即使 changes 为空。当前 prototype 的 `freeze` 会将文件改为
`.frozen.json`，但这是可选归档，不是协议要求。`recent` 先读取
Conversation Deltas，再 fallback 到 legacy；`rebuild-context` 打包
`PROJECT.md`、recent semantic deltas、empty conversation metadata 和
legacy fallback。

原型不调用模型，不自动从对话提取变化，不提供数据库、RAG、锁服务、reducer 或自动摘要服务。

## 14. 当前证据与版本定位

DeltaLayer v0.2.1 是 Open Design Proposal + Experimental Prototype，不是成熟插件发布。

当前现实仍由 source、tests、Git 和 workspace 提供：

```text
              Current Reality
        Source / Tests / Git / Workspace
                    |
                    | validate against
                    v
            PROJECT.md
          rebuildable current view
                    ^
                    |
       +------------+------------+
       |                         |
 Conversation A              Conversation B
       |                         |
       v                         v
    Delta A                    Delta B
```

Delta 是连续性输入和历史证据，不是当前实现的 source of truth。

此前公开证据包括：

- **Workbench Case 1**：真实 cross-conversation continuation；
- **Qicetai Case 2**：unstable external dependencies 下的 temporal semantic evolution；
- QCT retrospective 48 deltas、Phase 4 和 H5。

这些案例发生时使用的是共享 append-only `changes.jsonl`。它们帮助暴露了 current view、时间精度和历史边界问题，并促成 conversation-granularity model，但不证明它们当时已经使用了 per-conversation files。

**H5 仍为 `PARTIALLY_SUPPORTED`。** 现有证据不证明总 token 成本下降、长期可靠性、所有 Agent 的正确时间解释或 Conversation Delta 优于高质量 handoff。

## 15. 不是什么

DeltaLayer v0.2.1 不是：

- memory database；
- RAG system；
- vector store；
- execution transcript；
- event-sourcing runtime；
- deterministic reducer；
- governance or authority system；
- source-of-truth for code；
- 自动摘要服务。

当前实现继续由源码、测试、Git 和实际 workspace 体现。DeltaLayer 只保存有长期意义的项目语义差异，并把历史解释交回给 LLM。

## 16. 最终原则

> **A Conversation Delta is a semantic change record owned by one conversation.**

每个 conversation 都留下一个 Delta 文件，哪怕它为空。

> **A conversation owns exactly one Delta during its lifetime.**

当前对话可以修订自己的净变化；另一个 conversation 不得接管这个 Delta。

> **Owned Delta may change; historical Delta is not another conversation's write target.**

> **The current conversation may revise its own delta. Past conversations may not.**

> **New Conversation Deltas first; legacy history remains readable.**

新模型优先读取 Conversation Delta，旧 shared JSONL 继续只读兼容。

> **Writers should be precise; readers should be tolerant.**

写入尽量精确，读取不要因为粗糙时间元数据丢掉语义历史。

> **Persist change ownership, not context. Let the next model reconstruct the rest.**
