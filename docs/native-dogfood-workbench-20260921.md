# Native Dogfood Case 1 — AI Game Workbench

**日期：2026-09-21。项目：AI Game Workbench。接力 Agent：Codex。**

这是一次真实开发中的项目连续性接力记录，不是受控 benchmark，也不是普遍可靠性证明。案例覆盖 Audit → Repair → Validation → Release preparation 四个阶段。

## 背景与证据范围

据项目操作者确认，每一阶段使用全新的 Codex 对话，没有继承前一段聊天上下文，用户也没有重新复述项目状态。跨对话连续性由仓库中的三个文件提供：

```text
AGENTS.md
PROJECT.md
.deltalayer/changes.jsonl
```

这不意味着 Agent 只读三个文件就完成开发。源码、测试、Git 和实际工作区仍用于验证当前现实，再决定和实施修改。

本材料将两类依据分开：

- **文件可核验的记录：** [在线变化历史](../evidence/workbench-20260921/changes.jsonl)、[阶段最终视图](../evidence/workbench-20260921/project-final.md)及[规则快照](../evidence/workbench-20260921/agents-final.md)。其中的测试和构建结果是当时 Agent 写下的结果，本次归档没有重新执行它们。
- **操作者确认的过程观察：** 新对话之间不继承聊天、用户未复述背景、Agent 主动读视图和最近变化、主动清除陈旧视图。原始会话和工具读取转录未公开，这些过程事实不能仅凭最终文件独立重放。

[提示词记录](../evidence/workbench-20260921/prompts.md)保存三条已确认的真实用户原文。D 阶段只确认了任务意图，未保存精确原文，没有补造引文。

## 真实接力链路

下面时间均为 `+08:00` 的**变化记录写入时间**，不是对话开始时间或任务耗时。A/B/C/D 是本案例的叙述标签，不是历史文件中的 Agent ID。

### 起点：启用 Native Dogfood

第 1 条记录，18:02:16，说明实际 Workbench 仓库启用了自举式 `AGENTS.md`、可重建视图及只追加历史。它明确写明没有回填旧变化，也没有修改业务代码。

该起点视图使用了此前用户提供的审计背景；“用户无需复述”指后续接力阶段，不表示项目最初没有人类提供背景。此处指真实实现仓库，不是桌面的文档导出副本。

### Agent A — Audit

用户提示：

> 做一个审计，然后告诉我接下来应该干嘛。

A 审计当前工作区，发现 reconfirm 流程、Migration 032、历史 fixture 和 App 工作区前置条件等问题，更新 `PROJECT.md` 并追加变化。

第 2 条记录，18:11:40，保留当时的红色基线：

- 默认全套暴露 27 个 Storage 失败和 5 个 App 失败。
- Migration 032 新增列但没有推进 `PRAGMA user_version`。
- 历史 fixture 在列尚不存在时调用了最新 repository contract。
- 部分 App fixture 未建立 governed Project World，进入 setup 而非预期 workspace。
- 默认跳过的真实 provider B1 测试不能被当作已通过。

审计没有修改业务代码。记录既留下优先问题，也没有把调查包装成修复。

### Agent B — Repair

新对话收到的提示只有：

> 修复当前最优先的问题，完成必要回归，然后告诉我下一步。

据操作者观察，B 自行从连续层恢复优先级，没有要求用户复述 A 的问题清单。第 3 条记录，18:37:03.3760821，记下：

- 修复 Remove → reopen → reconfirm，保留 Authority history，仅在确认后清除 setup 标记。
- 修复 Migration 032 版本推进和历史 fixture 兼容性。
- 修正旧删除测试，使其符合当前 soft-removal 合同。
- Storage 恢复 **321/321**。
- App 仍为 **698 passed / 5 failed / 5 skipped**，剩余失败原因被明确留给下一任。

这些是 B 在线追加的 semantic changes，不是本次为了案例而重建的历史。

### Agent C — Validation

新对话收到：

> 继续处理当前剩余问题，完成必要验证，然后告诉我下一步。

据操作者观察，C 先读取 `PROJECT.md` 和最近变化，再检查源码和测试。第 4 条记录，19:11:48，记下：

- 修完剩余 App fixtures，使其先建立 governed Project World。
- App 为 **704 passed / 0 failed / 5 skipped**。
- 默认全套为 **1,251 passed / 0 failed / 6 skipped**，构建 **0 warnings / 0 errors**。
- Worker handoff 解析支持 provider 的 camel-case 字段。
- 修正验收 fixture 后，**Codex 三轮真实 Worker 验收通过**。
- **OpenCode + DeepSeek B1 Claim/Handoff/Authority 验收通过**。
- Release packaging 仍待处理，没有被宣称完成。

操作者同时观察到 C 主动修订或删除 `PROJECT.md` 中失效的 current-state 描述。最终视图不再把已修复回归当作当前 blocker，旧失败则仍保留在变化历史中。

这里的“Codex 三轮验收”是 Workbench 产品内部的 Worker 验收，不是 A/B/C/D 这四次新对话；OpenCode/DeepSeek 是产品验收路径，也不代表已经验证了不同 Agent 家族之间的连续性接力。

### 运行中的规则澄清

第 5 条记录，19:15:40，明确强化了 `PROJECT.md` 维护规则：新事实取代旧事实时修订或删除陈旧描述，冲突时核实现实，交接前做轻量一致性检查。

这条记录原样保留，不能为叙事方便删掉。附带的 `agents-final.md` 是澄清之后的快照，不代表每个阶段都使用了完全相同的规则。本案例因此不能隔离证明“未经任何维护提示的最小协议”产生了全部行为。

### Agent D — Release Preparation

又一个新对话中，用户仍只要求继续剩余工作；精确原文未保存，不提供逐字引文。

据操作者观察，D 从连续层识别当前工作已进入 release preparation，随后核实实现、打包并验证。第 6 条记录，19:34:14.4345580，记下：

- 完成 Windows 本地候选 `alpha-rc.20260921-local.1` 的打包与 manifests。
- 加固 publish、安装和卸载边界，**11 项 distribution smoke 通过**。
- Release solution build 为 **0 warnings / 0 errors**；新的全套 TRX 结果仍为 **1,251 passed / 0 failed / 6 skipped**。
- 候选来源是已有 commit 加未提交修改，属于 **dirty working-tree candidate**，不是 committed release candidate。
- 没有 commit、tag、push 或外部发布；下一步仍需审阅并提交源码、从该 commit 重建候选和完成发布 gates。
- 当天较早的 provider passes 没有被冒充为打包候选的新 provider certification。

D 更新了当前视图并追加历史，没有错误地宣布“已经可以发布”。

## 观察到的闭环

```text
Read → Understand → Verify → Act → Test → Persist → Handoff
```

据本次操作者观察，fresh Agent 主动读取当前视图和最近变化，采用 recent-first，而非恢复完整聊天历史；随后仍以源码、测试、Git 和工作区核实并继续真实开发。

六条在线记录按时间保留了红色基线、部分修复、验证通过和候选打包边界，符合本次 append-only 使用方式。`PROJECT.md` 则作为可修改的 current view 主动清除了过时状态。**单份末态快照本身不能独立证明每次文件操作都未改写旧行**，也没有保存可用于精确量测回溯深度的全部读取轨迹。

用户无需在接力提示中点名 P0、Migration 032、governed Project World、Provider B1 或 release candidate，也没有在这些提示里提醒 DeltaLayer 文件名。

## 有限结论

> A fresh Codex conversation successfully recovered prior project priorities from repository-local continuity artifacts and continued real development work without the user restating project history.

这句话描述的是本案例中报告并记录的成功接力，不是协议对任何后续任务的保证。

> Across several fresh Codex conversations, the observed Workbench dogfood maintained a usable development handoff through PROJECT.md and append-only semantic changes.

与此前 QCT retrospective reconstruction 不同，这里的变化是在真实开发过程中 native online 写入，不是事后 backfill。原始 QCT 压缩统计和 H5 成本问题是另一组证据；**H5 仍为 `PARTIALLY_SUPPORTED`**。

## Limitations

- **One real project:** 仅一个真实项目，不能推广到所有项目。
- **Primarily one agent family:** 接力主体是 Codex；产品 provider 验收不等于跨 Agent 家族连续性实验。
- **One day of observation:** 仅 2026-09-21 当天。
- **Small native history so far:** 当前快照仅 6 条记录；不能推出长历史也同样可用。
- **No long-horizon degradation evidence yet:** 没有长期遗漏、过早停止或视图漂移的退化数据。
- **No broad multi-agent concurrency evidence yet:** 没有广泛并发写入、冲突或权限消解证据。
- 没有同任务受控对照，也没有总 token、总源码读取量或净时间节省测量。
- 会话新鲜度、读取行为与视图修订由操作者确认；完整会话、读写轨迹、各阶段视图差异和测试原始输出未公开。本次没有重新执行产品测试。
- 规则在运行中有过澄清，不能把全部结果归因于未变化的初始提示。

本案例没有证明所有 Agent continuity 问题已解决、memory/RAG 已无必要、普遍显著节省 token，或长期可靠性已经成立。

## Evidence

[证据说明与脱敏边界](../evidence/workbench-20260921/README.md) · [真实提示词](../evidence/workbench-20260921/prompts.md) · [在线历史](../evidence/workbench-20260921/changes.jsonl) · [最终视图](../evidence/workbench-20260921/project-final.md) · [规则快照](../evidence/workbench-20260921/agents-final.md)
