# DeltaLayer v0 正式设计规范

## 1. 定位

DeltaLayer 是一个面向长期 LLM / Agent 工作的轻量项目连续层。

它不试图保存完整对话，也不试图构建复杂的长期记忆系统。

它只保存一类信息：

> **项目发生了什么变化。**

其核心思想是：

> **Persist change, not context.
> Let the next model reconstruct the rest.**

中文：

> **保存变化，而不是保存上下文；剩下的，让下一任模型自己重建。**

---

# 2. 要解决的问题

长期 Agent 项目通常存在以下问题：

* 新 Session 不知道之前发生过什么；
* 新 Agent 需要重新扫描大量源码；
* 用户需要重新解释项目背景；
* 完整聊天历史 token 成本高；
* 长上下文包含大量已经废弃的方案和过程噪声；
* 不同 Agent 之间交接困难；
* 项目历史越长，重新建立项目理解的成本越高。

现有方案通常通过以下方式解决：

* 保存完整 Session；
* Session Summary；
* 长期 Memory；
* 向量数据库；
* RAG；
* Current State；
* Handoff 文档；
* 状态机；
* Event Projection；
* 复杂治理。

DeltaLayer v0 提出一个更小的假设：

> **一个长期项目真正需要跨 Agent 保留下来的主要信息，可能不是完整历史，而是每一次有意义的语义变化。**

---

# 3. 核心数据结构

DeltaLayer v0 只有两个核心持久化对象：

```text
changes.jsonl
PROJECT.md
```

以及一份 Agent 行为规范：

```text
AGENTS.md
```

整体结构：

```text
project/
├── AGENTS.md
├── PROJECT.md
└── .deltalayer/
    └── changes.jsonl
```

---

# 4. changes.jsonl

`changes.jsonl` 是 DeltaLayer 中最重要的数据。

它保存项目的语义演化历史。

它应当：

* append-only；
* 按时间保存；
* 不主动删除旧变化；
* 不因为后来出现新方案而修改旧记录；
* 允许互相矛盾的历史变化同时存在。

例如：

```json
{"time":"2026-09-21T09:30:00+08:00","source":"codex","changes":["决定使用方案 A 作为当前实现方向"]}
{"time":"2026-09-21T11:10:00+08:00","source":"codex","changes":["方案 A 在真实验证中存在问题，当前改为方案 B"]}
{"time":"2026-09-21T14:20:00+08:00","source":"codex","changes":["方案 B 仍无法满足约束，当前采用方案 C"]}
```

未来 Agent 不需要额外的冲突解决器。

它可以直接理解：

> A 曾经成立，后来改为 B，最终又改为 C。

---

# 5. Change 的定义

Change 不是：

* 工作日志；
* Session Summary；
* 工具调用记录；
* 推理过程；
* TODO 列表；
* 完整任务报告。

Change 表达的是：

> **某个时刻以后，项目世界与之前相比发生了什么具有持续意义的变化。**

典型 Change 包括：

### 能力变化

```text
支持 PDF 导入。
```

### 缺陷状态变化

```text
修复 History reopen 后 verification 状态丢失的问题。
```

### 架构变化

```text
主查询链由 RAG 调整为结构化数据库 + SQL。
```

### 决策变化

```text
放弃方案 A，改用方案 B。
```

### 重要事实被确认

```text
History replay 不会重新执行 verification。
```

### 项目方向发生变化

```text
当前开发重点由数据导入转向分析能力。
```

### 旧假设失效

```text
此前认为 Provider fallback 已完整覆盖，但真实测试证明 native runtime 仍缺少严格参数校验。
```

---

# 6. 什么不应该写入 Change

以下内容默认不进入长期变化层：

```text
阅读了 12 个文件。
运行了 pytest。
尝试了三个方案。
发现一个函数。
重新启动了服务。
做了浏览器测试。
调查了数据库结构。
```

这些可能对完成当前工作有帮助，但如果没有改变长期项目语义，就不属于 Change。

核心判断标准：

> **如果未来 Agent 永远看不到本次完整对话，这条信息是否仍然值得它知道？**

如果答案是否定的，则通常不应写入。

---

# 7. Change 的写入时机

DeltaLayer v0 不要求将 Change 限定在 Session 结束或某一种固定生命周期边界。

Agent 可以根据语义判断，在项目发生有意义变化时留下 Change。

例如：

```text
10:00
选择方案 A
→ 可以记录

11:00
发现 A 不成立，切换到 B
→ 可以记录

13:00
B 验证失败，最终切换到 C
→ 可以记录
```

这些都是真实的项目演化。

不要求只保留最终 C。

因此：

> **Change 保存演化，而不是只保存最终结论。**

---

# 8. Change Side Channel

Agent 正常工作时，应始终具有一个额外的结构化输出通道：

```json
{
  "changes": []
}
```

正常用户输出与 Change 输出是两个不同通道。

例如：

```text
用户可见：

功能已经完成，相关测试通过。
```

后台：

```json
{
  "changes": [
    "native runtime 新增严格工具参数校验",
    "非法参数现在会在进入 Evidence Workspace 前被拒绝"
  ]
}
```

如果没有值得保留的长期变化：

```json
{
  "changes": []
}
```

空数组必须被视为完全正常的结果。

DeltaLayer 不应该鼓励 Agent 为了“必须写东西”而制造低价值记录。

---

# 9. Change 最小 Schema

v0 推荐：

```json
{
  "time": "2026-09-21T15:30:00+08:00",
  "source": "codex",
  "conversation_id": "optional",
  "changes": [
    "..."
  ]
}
```

其中：

### `time`

变化写入时间。

### `source`

变化来源，例如：

```text
codex
claude
chatgpt
human
ci-agent
```

### `conversation_id`

可选。

用于需要时回到原 Session。

不作为连续性工作的必要信息。

### `changes`

一条或多条语义变化。

---

# 10. PROJECT.md

`PROJECT.md` 保存当前项目的高密度语义视图。

例如：

```markdown
# Project

## Goal

构建一个可验证的结构化数据问数与分析系统。

## Current Architecture

- 结构化数据作为确定性问数主链
- LLM 负责意图理解
- SQL / 规则引擎负责确定性计算
- Evidence Workspace 负责证据链
- Verification 负责独立复核

## Current Stage

正在推进 v0.7 native runtime 稳定性。

## Recently Completed

- History replay 可恢复验证状态
- native runtime 已增加参数校验

## Known Constraints

- 不允许根据 COMPLETED 状态猜测 verification
- Report / Chart / Export 只能消费 Verified Claim

## Open Areas

- Provider failure 边界
- runtime 参数和 provenance 一致性
```

---

# 11. PROJECT.md 的地位

`PROJECT.md` 不是最高权威。

它只是：

> **当前项目语义状态的可重建视图。**

换句话说：

```text
changes.jsonl
= durable semantic history

PROJECT.md
= disposable materialized view
```

如果 `PROJECT.md`：

* 过时；
* 错误；
* 被删除；
* 内容发生冲突；

系统仍然可以通过：

```text
changes.jsonl
+
LLM
```

重新生成它。

因此：

> **Changes 保存历史，PROJECT.md 保存方便。**

---

# 12. 为什么仍然保留 PROJECT.md

理论上，新 Agent 可以只读 Change。

但随着项目长期运行，changes.jsonl 可能逐渐增长。

即使总数据量仍然很小，大多数 Agent 也没必要每次重新理解全部历史。

因此加入一个轻量当前视图：

```text
PROJECT.md
```

可以把 cold start 成本进一步降低。

理想启动层级：

```text
PROJECT.md
↓
Recent Changes
↓
Older Changes
↓
Source / Git / Task Body
```

每一层仅在上一层信息不足时继续深入。

---

# 13. 新 Agent 的启动行为

新 Agent 进入项目后：

## Step 1

首先读取：

```text
PROJECT.md
```

获得项目当前概览。

## Step 2

读取最近的 Change。

例如最近：

```text
3～5 条
```

但这一数量不是固定规则。

## Step 3

Agent 自己判断：

> 当前上下文是否足够完成任务？

如果足够：

```text
STOP READING HISTORY
```

开始工作。

如果不足：

```text
继续向更早 Changes 回溯
```

直到模型认为：

> 已经理解到足够安全、正确地继续工作。

---

# 14. Model-Decided Retrieval Depth

DeltaLayer 不设固定历史读取深度。

不规定：

```text
top_k = 10
```

也不规定：

```text
始终加载最近 50 条
```

因为不同任务需要的历史深度不同。

实际实验已经观察到：

```text
某个任务：
3 条不够
→ 继续读到 8 条
→ Agent 判断足够

另一个任务：
3 条已经够
→ 直接停止
```

因此读取原则是：

> **Recency-first, model-decided depth.**

中文：

> **最近优先，读取深度由模型自行决定。**

---

# 15. 不使用源码作为项目历史数据库

源码负责回答：

> **现在真实存在什么？**

Changes 负责回答：

> **为什么会变成现在这样？**

因此：

```text
Source Code
= present implementation

Changes
= semantic evolution
```

新 Agent 不应为了恢复项目背景而默认扫描整个仓库。

正确顺序是：

```text
PROJECT.md
↓
Changes
↓
建立项目地图
↓
只读取完成当前任务所需的相关源码
```

但当 Change 与实际源码发生冲突时：

> **当前源码、测试结果和实际工作区仍然代表当前现实。**

Change 不是代码事实数据库。

---

# 16. 外部变化与缺失历史

真实项目可能被以下主体改变：

* 人工修改；
* Git merge；
* 其他 Agent；
* CI；
* 未接入 DeltaLayer 的工具。

因此可能出现：

```text
Changes:
数据库仍为 SQLite

现实：
源码已经是 PostgreSQL
```

这不被视为系统崩溃。

Agent 应理解：

> 存在尚未记录或尚未读取的变化来源。

随后可自行：

* 查看 Git；
* 查看其他 Agent Changes；
* 检查源码；
* 询问用户。

并可以留下新的 Change：

```text
检测到此前未记录的外部变化：数据库已从 SQLite 迁移至 PostgreSQL。
```

---

# 17. 并行 Agent

多个 Agent 可以同时产生 Change。

例如：

```json
{"time":"10:31","source":"codex-A","changes":["认证模块增加 token refresh"]}
{"time":"10:32","source":"codex-B","changes":["数据库新增 migration 021"]}
```

DeltaLayer v0 不要求提前计算：

* merge；
* branch；
* authority；
* precedence。

未来 LLM 根据：

* 时间；
* 来源；
* Change 语义；

自行理解并行关系。

如果两个并行任务产生真正冲突：

```text
Agent A：
Session 存储迁移到 Redis。

Agent B：
继续扩展数据库 Session。
```

后续 Change 可以记录真实收敛结果：

```text
发现两条并行实现冲突，最终统一采用 Redis Session。
```

---

# 18. AGENTS.md 规则

推荐加入：

```markdown
## Project Continuity

This project maintains an LLM-native semantic change history.

### When starting work

1. Read `PROJECT.md`.
2. Read the most recent semantic changes.
3. If the current project context is not sufficient to safely and correctly perform your work, continue reading older changes in reverse chronological order.
4. Stop reading history when you judge that you understand enough to proceed.
5. Do not scan the full repository merely to reconstruct project history.
6. Use source code, tests, Git, and the actual workspace to verify the present implementation when needed.

### While working

Maintain a `changes[]` side channel.

Whenever you determine that the project has undergone a durable semantic change, append a concise change record.

Changes may include:
- capabilities added or removed;
- bugs fixed;
- architecture changed;
- decisions changed;
- important facts established;
- old assumptions invalidated;
- project direction changed.

Do not record:
- reasoning;
- temporary investigation;
- tool activity;
- failed attempts with no lasting relevance;
- unchanged information.

`changes: []` is valid when nothing durable changed.

### Current project view

`PROJECT.md` is a convenient current semantic view, not immutable truth.

When your work or newly-read changes materially alter the current project understanding, update `PROJECT.md`.

The semantic change history is durable. `PROJECT.md` must remain reconstructable from project history and current reality.
```

---

# 19. DeltaLayer 不是什么

DeltaLayer v0 不是：

### Memory Database

它不试图记住用户和世界中的所有事实。

### RAG System

它不通过 embedding 做默认检索。

### Vector Store

v0 不需要向量数据库。

### Logging System

它不保存所有操作事件。

### Session Summary System

它不总结每次对话。

### Event Sourcing Runtime

它不要求 deterministic reducer。

### Governance System

它不要求 authority、approval 或 conflict resolver。

### Source-of-Truth for Code

当前实现仍然由源码、测试和现实工作区体现。

---

# 20. v0 明确不加入的能力

除非真实实验证明有必要，v0 不加入：

* embedding；
* vector database；
* semantic search；
* RAG；
* memory scorer；
* summary tree；
* reducer；
* deterministic projection；
* branch；
* merge；
* authority；
* conflict resolver；
  -云服务；
  -复杂数据库；
  -独立总结 Agent。

原则：

> **没有实验需求，不增加基础设施。**

---

# 21. 当前实验支持

目前已有实验给出以下有限证据。

## Change 可生成

长期 Agent 可以在正常工作之外额外生成结构化变化字段。

## Change 信息密度较高

48 个真实开发任务中：

```text
Task 最终消息：
40,555 字符

Delta JSON：
10,398 字符

纯 changes：
4,585 字符
```

纯语义变化约为同组最终消息字符数的：

```text
11.3%
```

该比例尚不是完整 Session 压缩比。

## Agent 能自主控制回溯深度

真实实验中出现：

```text
3 → 8 → stop
```

以及：

```text
3 → stop
```

两种读取模式。

## Delta 可作为真实开发前置上下文

已有真实任务完成：

```text
Delta
→ Source
→ Tests
→ Patch
```

未观察到 Delta 导致明显错误先验。

## 当前限制

尚未证明：

* Delta 显著降低总体 token 成本；
* Delta 显著减少所有类型的源码考古；
* Delta 在所有长期项目中优于高质量 handoff/summary。

因此当前定位应保持为：

> **低成本项目连续性 primitive。**

而不是：

> 已被证明优于所有 Agent Memory 系统的通用方案。

---

# 22. 核心价值

DeltaLayer 主要追求四个价值。

## Continuity

新 Agent 不必完全重新认识项目。

## Compression

无需把整个过去重新塞入上下文。

## Semantic Stability

减少已经废弃的方案、过程噪声和长上下文造成的语义干扰。

## Handoff

Codex、Claude、GPT 或未来其他 Agent 可以通过同一份变化历史继续工作。

---

# 23. 设计哲学

传统长期记忆系统通常试图：

> 让基础设施替模型理解历史。

DeltaLayer 采取相反方向：

> **让基础设施保持极笨，让 LLM 保持极聪明。**

基础设施只负责：

```text
保存变化
记录时间
记录来源
提供历史
```

模型负责：

```text
理解新旧关系
理解废弃和替代
理解并行
判断读取深度
重建当前项目模型
决定下一步工作
```

---

# 24. 最小闭环

DeltaLayer v0 的完整闭环可以压缩成：

```text
           PROJECT.md
                │
                ▼
        New Agent Starts
                │
                ▼
          Recent Changes
                │
          context enough?
          ┌─────┴─────┐
         yes          no
          │            │
          │       Older Changes
          │            │
          └──────┬─────┘
                 ▼
               Work
                 │
        meaningful change?
          ┌──────┴──────┐
         yes            no
          │              │
   append changes       nothing
          │
          ▼
     update PROJECT.md
       when useful
```

---

# 25. 最终原则

DeltaLayer v0 可以被压缩成四句话：

> **Every meaningful change leaves a trace.**

每一个有意义的变化都留下痕迹。

> **History is append-only.**

历史只追加，不重写。

> **Future agents read backward until they understand enough.**

未来 Agent 从最近变化向过去读取，直到自己认为足够。

> **Current state is a view, not the history itself.**

当前状态只是历史的一个视图，不是历史本身。

最终：

> **Persist change, not context.
> Let the next model reconstruct the rest.**
