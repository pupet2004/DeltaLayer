# Native Dogfood Case 2 — Qicetai
## Temporal Semantic Evolution Under Unstable External Dependencies

**日期：2026-09-21。项目：Qicetai。连续性维护环境：Codex；产品内真实模型调用：DeepSeek。**

本案例观察的是不稳定外部依赖下的语义状态演化，不是跨 Agent 数量，也不是受控 benchmark。

> Can an append-only semantic change history preserve a project whose real state repeatedly changes because of external dependencies, without rewriting prior history or requiring a deterministic reducer?

## 证据范围

本次保存[九条 native online 变化](../evidence/qicetai-20260921/changes.jsonl)、[阶段最终视图](../evidence/qicetai-20260921/project-final.md)和[规则快照](../evidence/qicetai-20260921/agents-final.md)。它们来自实际开发仓库，不是此前 QCT 48 条 retrospective corpus 的补充重建。

操作者确认这些变化在实际开发中在线产生。本次从现有文件归档，仅脱敏一处安装路径，没有回填事件、修正旧时间或重写 change 的语义。没有可靠保存的精确用户提示词随本次材料提供，因此不创建猜测性的 `prompts.md`。

下述测试和真实模型调用结果来自当时 Agent 留下的记录及当前视图，本次归档没有重跑 Qicetai 产品测试或外部请求。原始会话、网络日志、测试输出和私有源码未公开；文件中的历史报告不等于完整、可独立重放的实验轨迹。已核对本地 Git 中修复 commit 的编号与标题。

## 实际演化

前七条记录使用 `+08:00` 写入时间。最后两条只有日期，下面按原始 JSONL 行序呈现，不推测它们的具体时刻或耗时。

| 行 | 原始 `time` | 记录中的变化与边界 |
| --- | --- | --- |
| 1 | `2026-09-21T17:33:28+08:00` | 初始化根目录连续性规则、当前视图和 append-only history |
| 2 | `2026-09-21T18:05:00+08:00` | 加入 SearXNG adapter；本机没有可用实例，live search 尚待验收 |
| 3 | `2026-09-21T18:42:00+08:00` | 独立 Windows SearXNG 安装、启用 JSON 后，live search / DeepSeek external research 通过 |
| 4 | `2026-09-21T19:03:13+08:00` | 加入 atomic `read_web_page`，85 项回归通过；模型自主调用 reader，但 synthetic DNS 导致拒绝 |
| 5 | `2026-09-21T19:52:34+08:00` | 网络变化使 standalone 页面读取恢复；随后模型搜索八次均为空，完整链路仍未通过 |
| 6 | `2026-09-21T19:56:31+08:00` | 页面 reader 提交为 `8bbc6a3`；提交本身不代表 live 链路通过 |
| 7 | `2026-09-21T20:30:58+08:00` | 独立搜索设置调整后最终 35/35 nonempty；模型选中两个网页，Fake-IP 再次导致读取拒绝 |
| 8 | `2026-09-21` | 加入 independent A/AAAA DoH validation；记录 VPN/Fake-IP 下完整 search -> page -> answer 通过 |
| 9 | `2026-09-21` | 修复提交 `e15bb23`；最终 183 项 focused/regression tests 通过 |

### 从 Search 可用到 Page Read 被拒绝

最初加入的是现有 `WebResearchService` 的 HTTP-only SearXNG adapter。没有运行实例时，变化明确写下 live acceptance pending。安装和配置独立 Windows 实例后，搜索及 external-research 流程一度通过；这不是后来才加入的 page-body retrieval 已经通过。

加入 atomic `read_web_page` 后，DeepSeek 自主选择 reader。选中 hostname 被解析到 `198.18.1.26`，SSRF 防护返回 `URL_NOT_ALLOWED`；standalone 读取也复现拒绝。85 项回归通过并没有被混同为真实网页读取验收通过，防护也没有为通过验收而放松。

### 临时恢复与再次失败

用户改变本地网络后，公共 DNS 返回 public addresses，未改动源码的 standalone 读取一度恢复，包括此前失败页面的 2,771 字符内容。

但下一次 fresh-process DeepSeek 测试做了八次搜索，全部为空，没有调用 reader。记录中的 SearXNG 检查发现上游 engine timeouts。因此，“单页读取恢复”与“完整 autonomous chain 仍失败”在同一阶段可以同时成立。

之后只调整独立 SearXNG settings，保留 Google CSE 和 360search，engine budget 为 6 秒。最终重复查询为 10/10，A-E 各 5/5，合计 **35/35 nonempty**；另有未改动 Qicetai search 的 **5/5**。

不能把恢复全归因于设置调整：该条 change 明确记载，调整前基线已经是 10/10。Google CSE 仍会 rate-limit，严格 NEWS 过滤也未被支持。这些限制原样保留。

随后 DeepSeek 做了八次非空搜索，自主选择两个页面，但 synthetic DNS 再现，两个读取均遭拒绝。模型披露只能使用 snippets；完整 page-reading chain 再次失败。

### URL Safety Boundary 的修复

没有全局 whitelist `198.18.0.0/15`，也没有放开 private/redirect SSRF 防护。修复仅在 URL safety boundary 加入 independent A/AAAA DoH validation，以独立结果判断 hostname 是否指向公共地址。

当时记录及操作者报告的结果为：

- VPN/Fake-IP 保持开启时，public hostname standalone read **PASS**。
- private、literal Fake-IP、metadata/reserved、unsafe redirect 及 DNS failure 拒绝边界被保留；相应安全回归通过。
- 原有 **85 tests** 未改动，新增 **98 security cases**，最终 **183 passed**。
- fresh-process DeepSeek 自主搜索两次，读取中国政府公开出版物的 **10,353 字符**，随后回答；完整 **search -> page -> answer PASS**。
- 未改 agent runtime、system prompt、tool schema、VPN 或 SearXNG settings。

修复提交：

```text
e15bb23
fix(v0.7): support safe webpage reads behind fake-ip proxies
```

这不是全面 SSRF 安全证明。最终视图明确保留限制：原 hostname 路由依赖 VPN/proxy forwarding，没有 socket pinning，也不保证覆盖所有连接时 DNS race 或恶意代理。常驻 API 尚未重启到新代码，成功链路使用的是 fresh Python process。

## 历史事实不因后来变化而变成错误

```text
synthetic DNS -> page read rejected
network changed -> standalone page read recovered
engine timeouts -> autonomous chain failed
search became usable -> synthetic DNS rejected reads again
DoH validation -> current-source chain passed under Fake-IP
```

这些是不同时间、不同验证范围的事实，不是必须互相覆盖的矛盾答案。旧的失败记录当时是真实的；后来的恢复不要求把旧记录改成“已经成功”。

变化历史保留先后演化，`PROJECT.md` 汇总当前能力与仍存在的边界。最终视图记录了修复和 183 项通过，也保留常驻进程、代理信任与上游稳定性限制。源码、测试、Git 和实际工作区仍负责验证当前现实。

从操作者报告及留下的文件看，模型在工作中区分了早期失败、短暂恢复、再次失败和后续安全边界修复，而没有要求改写旧事件或新增 deterministic reducer。**末态文件本身不能证明每次读写都遵守 append-only，也没有提供每次模型读取与推理的独立轨迹。**

## Dogfood Finding: Timestamp Precision

前七条有 offset-aware timestamp，例如：

```json
{"time":"2026-09-21T20:30:58+08:00"}
```

最后两条真实记录则都是：

```json
{"time":"2026-09-21"}
```

它们在公开副本中保持原样。单份 JSONL 的追加顺序仍保留先后，本次 native handoff 未报告因此失败；但日期不能提供同日时刻，降低同日排序、跨来源合并和后续 chronological retrieval / pagination 的确定性。文件行序不等于跨来源全局时钟。

初次归档仅明确写入建议：

> `time` SHOULD use an offset-aware ISO 8601 timestamp whenever available.

例如 `2026-09-21T21:43:12+08:00`，或带 `Z` 的 UTC 时间。不得凭空补造旧时间或时区，也不新增 sequence id、Lamport clock 或排序治理。

**初次归档时的 prototype 边界更严格：** `now_timestamp()` 已产生带 offset 的时间，`parse_timestamp()` 要求 timezone offset。date-only 虽是可解析 JSON，却不是当时 CLI 接受的事件时间。reader 会警告并跳过第 8、9 行，只返回前七条合规记录。这是 native 写入暴露的真实兼容性缺口。

初次归档更新了[设计指导](../DESIGN.md)、[原型说明](../prototype/README.md)、[独立 AGENTS 示例](../prototype/examples/AGENTS.md)和两个实际项目的规则，当时没有改动 prototype 行为或迁移历史。规则快照保留澄清前版本。

随后修复了 reader 对 date-only 的兼容：保留原始日期精度，不解释为午夜，不补造时区；单一 JSONL 以内的事件顺序由物理追加位置决定，完整游标按已有行号分页，不按 timestamp 重排。

> Native dogfood produced two valid semantic events with date-only timestamps. The initial prototype skipped them because its reader required full timestamps. The evidence was preserved unchanged; the reader was subsequently made tolerant of coarse timestamps while retaining append order as the event order within a history file.

修复后 **21/21 单元测试通过**，覆盖混合精度、重复日期、时间倒退、坏行、翻页期间追加及 2,500 条记录分页。对原始公开 corpus 的只读检查以多种页大小取回 **9/9** 条记录，没有警告、遗漏或重复；所有 evidence 文件的字节保持不变。证据目录中的说明保留初次归档时的观察，不随 reader 修复改写。

这落实了 **Writers should be precise; readers should be tolerant.** 写入仍建议使用 offset-aware timestamp；读取不应因日期精度较低而丢弃语义历史。时间仍是元数据，文件追加顺序不是跨来源全局时钟。这次修复验证的是读取与分页行为，不是新增的 Agent 可靠性证明。

## 有限结论

> Qicetai's native dogfood showed that append-only semantic changes could preserve several reversals in observed system state while PROJECT.md converged on the current state.

这为不稳定外部依赖下 semantic event history 仍有使用价值提供了一个真实案例，不是所有模型都会正确理解时间演化的证明。它也不证明 reducer 永远不需要、RAG/memory 已过时，或长期可靠性已经成立。

- **Case 1 / Workbench:** cross-conversation continuation。
- **Case 2 / Qicetai:** temporal semantic evolution under unstable external dependencies。
- QCT retrospective 48 deltas、Phase 4 和 H5 是此前的不同实验；本案例不改变其统计或结论。

**H5 仍为 `PARTIALLY_SUPPORTED`。**

## Limitations

- **One project:** 仅 Qicetai 的一次真实开发轨迹。
- **Short observation horizon:** 仅 2026-09-21 当天。
- **Primarily one model/agent environment:** Codex 维护连续性，DeepSeek 是产品内模型；没有据此验证广泛跨 Agent 家族接力。
- **Small native history:** 仅九条记录，其中末两条缺少具体时刻和时区。
- **External network behavior was unstable:** 暂时恢复与失败不足以确定全部外部因果。
- **No long-horizon degradation measurement:** 没有长历史退化、遗漏率或总 token 成本测量。
- **No broad concurrent-writer evidence:** 没有广泛并发写入、合并或全局事件排序证据。
- 没有受控对照；公开材料是脱敏文件与当时报告，不包括原始私有会话、网络响应或测试输出。本次没有重跑产品验收。
- date-only 行仍缺少具体时刻和时区。后续兼容修复使九条历史均可读取，但没有恢复缺失元数据，也没有证明跨来源全局排序。

## Evidence

[证据与脱敏说明](../evidence/qicetai-20260921/README.md) · [在线历史](../evidence/qicetai-20260921/changes.jsonl) · [最终视图](../evidence/qicetai-20260921/project-final.md) · [澄清前规则快照](../evidence/qicetai-20260921/agents-final.md)
