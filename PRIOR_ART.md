# 相关工作与贡献边界

资料核对日期：2026-09-21。下面依据项目作者的仓库或官方文档描述，不是性能评测，也不是穷尽式先例检索。

> DeltaLayer 不声称发明了 agent continuity、append-only log 或 handoff。它尝试验证的是一个更窄的假设：**semantic changes 是否可以成为项目连续性的最小原语，并把历史解释交回给 LLM。**

## 比较维度

重点不在“别人有没有记忆”，而在保存单位、读取方式、历史解释责任和当前视图的地位。

| 工作 | 官方材料描述的重点 | DeltaLayer v0.2 的取舍 |
| --- | --- | --- |
| PROJECTMEM [1] | 以 append-only 事件保存问题、尝试、修复和决策；支持 supersedes、summary 与预检查 | 只要求语义变化记录，不要求独立判断/预检查层；追加历史与保留被替代决策不是本提案独有 |
| Handoff / progress artifacts [2] | 为下一轮工作留下进度、Git 记录、功能清单与可运行环境 | 变化历史与当前视图分离；认真维护的 handoff 是必须保留的强对照 |
| Lead-Protocol [3] | 文件化 session open、checkpoint、session close 与可验证交接；关心所有权及并发安全 | 不把固定 session 生命周期或所有权裁决作为语义日志前提；这不免除底层写入安全责任 |
| Intent [4] | living spec 作为共享上下文，结合任务工作区和多 Agent 协调 | 不提供完整编排工作台；`PROJECT.md` 是可更新视图，不是历史本身 |
| claude-mem [5] | 捕获工具使用观察、生成语义摘要，并通过分层检索提供后续上下文 | 在产生工作时筛选持久变化，默认最近优先读取；不要求完整观察捕获与检索服务 |
| Mem0 [6] | 提供记忆对象的新增、搜索、更新等操作，支持更新既有记忆内容 | 对语义演化默认追加替代记录，不把旧变化改成最新答案 |
| LangGraph [7] | checkpointer 保存任务内图状态，store 保存跨任务数据 | 关注项目语义连续性，不替代执行恢复、容错或应用状态持久化 |

这些不是互斥选项。DeltaLayer 可以成为某个框架存储的数据格式，也可能与 handoff、spec、checkpoint 共存。不能由“默认不使用向量库”推出它比使用向量库的系统更高效。

## 最接近的重叠

PROJECTMEM、文件化 handoff 和 Lead-Protocol 都直接处理 coding agent 的跨会话连续性。它们让“用少量项目文件帮助下一个 Agent”无法被合理当成 DeltaLayer 的独创。

PROJECTMEM 已有 `events.jsonl → summary.md`，并通过 `--supersedes` 保留旧决策而记录替代关系 [1]。因此“历史追加而非覆盖”和“历史与视图分离”也不能被单独当作本提案的新意；值得检验的是更窄的记录选择与读取协议。

claude-mem 已经使用渐进式信息读取；DeltaLayer 不应声称发明了按需展开历史。区别在于本提案选择以时间倒序的语义变化为默认入口，并把停止回溯的判断交给模型。

Intent 的共享 spec 与 `PROJECT.md` 都提供便于阅读的项目理解，但本提案更强调把当前视图与不可因正常演化而覆写的历史分开。

这些都是结构上的对比，**不是已经验证的优势**。本项目没有对上述工具做直接实验，QCT 的 B 组只是该项目已有的 authority audit，不能代表所有 handoff 或 memory 产品。

## 不应使用的表述

- “首个解决 Agent 连续性的方案。”
- “别的系统都只保存 what happened。”
- “传统 memory 都必须使用向量数据库。”
- “LLM 天然能正确消解所有冲突。”
- “比所有 memory 系统节省 88.7% token。”

更准确的贡献描述是：**把已有思路收敛成一项极小的协议选择，并公开它目前受到支持和不受支持的实验边界。**

## 一手资料

以下为项目或作者发布的资料；网页会继续变化，本比较不等同于固定 commit 的源码审计。

1. PROJECTMEM: `https://github.com/riponcm/projectmem`
2. Anthropic, *Effective harnesses for long-running agents*: `https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents`
3. Lead-Protocol，作者项目说明及其链接的公开仓库：`https://devpost.com/software/lead-protocol-continuity-for-ai-coding-agents`
4. Intent 官方文档：`https://intentapp.dev/docs`
5. claude-mem 官方 README：`https://github.com/thedotmack/claude-mem`
6. Mem0 官方 Update 文档：`https://docs.mem0.ai/core-concepts/memory-operations/update`
7. LangGraph 官方 Persistence 文档：`https://docs.langchain.com/oss/python/langgraph/persistence`

v0.2 把保存单位从共享 event log 收窄为 conversation-owned Delta file：active conversation 可以更新自己的净变化，handoff 后冻结，legacy shared JSONL 只读兼容。这不是声称发明了 conversation/session artifacts、append-only history 或 handoff；它只是当前对最小存储边界的具体设计选择。

欢迎补充更早、更接近的协议、论文或工程实践，尤其是已经同时采用 semantic changes、conversation-level artifacts、模型自主回溯和可丢弃当前视图的工作。
