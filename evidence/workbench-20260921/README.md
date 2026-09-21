# Workbench Native Dogfood Evidence

案例日期与归档日期：2026-09-21。对应[案例文档](../../docs/native-dogfood-workbench-20260921.md)。

这是从真实 AI Game Workbench 实现仓库保存的 native dogfood 证据子集。不是桌面文档导出副本，不是事后重建的示例。操作者确认变化在当天真实任务中在线产生；本次整理不补写任何历史事件。

## Contents

| 文件 | 来源与公开处理 |
| --- | --- |
| [prompts.md](prompts.md) | 操作者确认的三条逐字提示；D 阶段明确标注未保存精确原文 |
| [changes.jsonl](changes.jsonl) | 来自实际仓库的 `.deltalayer/changes.jsonl`，6 条记录，原始 UTF-8 JSONL 字节不变 |
| [project-final.md](project-final.md) | 当天候选打包阶段的 `PROJECT.md`，仅将一处 canonical workspace 绝对路径替换为 `<WORKBENCH_REPO>` |
| [agents-final.md](agents-final.md) | 实际仓库 `AGENTS.md` 的原样快照，用于说明协议及运行中强化后的视图维护规则 |

源历史中没有需要脱敏的绝对路径、凭据值、个人信息或业务数据值，故 `changes.jsonl` 不重排、不重新序列化、不改写 change 文本。包括历史失败、维护规则变更、未提交候选状态和未完成 gates 的所有六条记录均保留。

`project-final.md` 是**该阶段 current view**，不是长期维护的最新状态页，也不是每阶段视图差异。其源文件在最后一条 change 写入前更新；两者描述的是同一候选打包阶段。

`agents-final.md` 保存的是末态规则，不能用它证明所有阶段的规则相同。19:15:40 的历史记录明确记载过一次视图维护规则澄清。

## Reading The History

记录时间均为 2026-09-21，时区 `+08:00`：

| 行 | 时间 | 记录性质 |
| --- | --- | --- |
| 1 | 18:02:16 | 实际实现仓库的 native bootstrap，没有回填旧历史 |
| 2 | 18:11:40 | A 审计：Storage/App 失败、Migration 032 与 fixture 问题 |
| 3 | 18:37:03.3760821 | B 修复：Storage 321/321，App 仍有 5 个失败 |
| 4 | 19:11:48 | C 验证：默认全套与单独启用的 provider gates；打包仍待办 |
| 5 | 19:15:40 | 运行中澄清 `PROJECT.md` 维护规则 |
| 6 | 19:34:14.4345580 | D 本地候选打包与发布边界；仍未提交/发布 |

这些时间不是会话开始时间，也不是任务耗时。

## Copy Integrity

原样归档的 `changes.jsonl`：5,116 字节，6 条非空 JSON 记录，UTF-8 无 BOM，LF 换行。

SHA-256：

```text
19432bd99e0e5987416850ffdb6a212b26db2836f564e1b138800dbd30298567
```

规则快照的 SHA-256：

```text
237f78be570aaf5f0545f4b373a0498c86a6f4cace2c43dc5485695c7d57e0cb
```

这些哈希用于检查归档副本一致性，不证明会话独立性、源事件正确性或历史从未被改写。最终视图的脱敏差异已逐字核对：仅 canonical workspace 路径替换，没有其他改写。

## Public Boundary

- 没有公开 Workbench 完整源码、源码片段、内部数据库、真实 fixtures、候选安装包、原始会话、credentials 或私人数据。
- 保留 Migration 032、组件名、测试数量、候选版本和基线 commit 标识等用户要求记录的工程事实；这些不是源码或数据库内容，也不是凭据。
- `project-final.md` 的路径占位符隐藏了 Windows 用户名和私有目录。原始绝对路径及替换映射不写入本目录。
- 文件中提及 credentials、manifest、数据库或 provider，仅是工程描述，没有导出其实际内容。
- 真实提示词由操作者确认；测试数字和构建状态来自在线记录，本次归档没有重新验证软件功能。

这组 evidence 支持此案例的有限观察，不代表普遍可靠性。只有一个真实项目、主要一种 Agent 家族、一天和很短的 native history；没有长期退化或广泛多 Agent 并发证据，也没有总 token 节省测量。

此前 H5 结论保持 **`PARTIALLY_SUPPORTED`**。本次只整理本地文件，不自动 push 或创建 release。
