# Qicetai Native Dogfood Evidence

案例与归档日期：2026-09-21。对应[Case 2 文档](../../docs/native-dogfood-qicetai-20260921.md)。

这是真实 Qicetai 开发仓库的 native online evidence 子集。操作者确认历史是在工作中在线生成，而非事后 backfill；它不同于此前 QCT 48 条 retrospective reconstruction。

## Contents

| 文件 | 来源与处理 |
| --- | --- |
| [changes.jsonl](changes.jsonl) | 实际 `.deltalayer/changes.jsonl` 的九条记录；只脱敏第 3 行的一处 Windows 安装路径 |
| [project-final.md](project-final.md) | 修复提交 `e15bb23` 阶段的 `PROJECT.md` 原样快照，无需脱敏 |
| [agents-final.md](agents-final.md) | 案例完成时、此次 timestamp 澄清前的 `AGENTS.md` 原样快照，无需脱敏 |

没有随本次材料提供可靠的精确用户提示词，不创建 `prompts.md`，不重构提示，也不导出原始 Session 来补足叙述。

## Fidelity And Redaction

- 第 3 行的本地 SearXNG 安装目录替换为 `<LOCAL_SEARXNG_INSTALL>`。不在公开材料中保存原路径或含用户名的映射。
- 除这一字符串替换，JSONL 的字节、行序、时间、source、change 文本、commit hashes 和测试数量保持不变；没有重新序列化、美化或补写事件。
- `project-final.md` 是该阶段 current view，不是持续更新页。`agents-final.md` 故意保留澄清前规则，不能拿后补规则冒充原有约束。
- 原 Qicetai history 与 `PROJECT.md` 在本次归档中不作修改。实际两个项目的 `AGENTS.md` 后续增加时间戳建议，不写回本证据快照。
- 保留 loopback 服务端点、synthetic DNS 地址、技术组件名和 commit 标识作为工程事实；没有复制凭据、客户/财报内容或页面正文。
- “local Qicetai logs”仅是原始文字中的泛称，不包含实际日志目录或日志内容。

脱敏后 `changes.jsonl` 的 SHA-256：

```text
534712f934c95cbc288aeb18c19a8ae09be09eb9dbc3bb7c2ca6fe2ea3ac99a1
```

`project-final.md` 的 SHA-256：

```text
e89bd5ad7527b53ff186d92c7961b0a7fddeb233039f21b176d6b8b83d3efeeb
```

`agents-final.md` 的 SHA-256：

```text
1201bdcae85638cdf3d6f2d5534692a52fae12bee7f99a796f138aa6dbb8f6c9
```

哈希仅用于副本一致性检查，不证明在线生成过程、每次历史写入或报告结果真实无误。JSONL 的路径脱敏差异另作逐字核对。

## Timestamp Finding

第 1-7 行使用 offset-aware ISO 8601 写入时间；第 8、9 行原本只有 `"time":"2026-09-21"`，此处原样保留。追加行序仍可用于阅读这份单文件的先后，但不能从缺失的时刻推导同日精确排序、跨来源合并顺序或可靠时间分页。

本次据此明确指导：

> `time` SHOULD use an offset-aware ISO 8601 timestamp whenever available.

这是后续写入建议，不是证据修复操作。没有补时间、补时区、增加 sequence id 或改动历史。

现有 prototype 自动生成带 offset 的时间，并严格拒绝缺少 timezone offset 的值。此文件的九行均为有效 JSON，但 **第 8、9 行不满足现有 CLI 时间校验**；CLI reader 会 warning 并跳过它们。不要把“native Agent 能读原始历史”混同为“prototype 已兼容全部历史”。本次不更改这一行为。

## Evidence Boundaries

- Workbench Case 1 观察跨新对话续接；本例观察外部依赖不稳定时的语义状态反转，不统计跨 Agent 数量。
- 历史记录包含失败、短暂恢复、再失败及最终修复。后来的通过不使早先失败成为错误记录。
- 35/35 nonempty 与随后 full-chain pass 是不同时点、不同验证范围；设置调整前已有 10/10 基线，不能把搜索恢复全部归因于调整。
- 183 tests、private/redirect 拒绝与真实 DeepSeek 链路来自当时报告，本次没有重跑 Qicetai 产品验收。独立 DNS 验证不是 socket pinning，也不是全面 SSRF 安全证明。
- 完整源码、内部数据库、业务数据、credentials、原始会话、网络响应及本地日志没有公开。
- 最终快照不能独立证明模型的每次读写行为；没有完整工具轨迹或逐阶段视图差异。

证据只支持本案例观察：一个项目、较短周期、主要一种 Agent 环境及九条 native history。外部网络不稳定，没有长期退化、广泛并发写入或总 token 节省测量。**H5 保持 `PARTIALLY_SUPPORTED`。**
