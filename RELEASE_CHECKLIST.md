# 发布前清单

当前目录是准备公开发布的材料包。发布目标：`pupet2004/DeltaLayer`，许可证：Apache-2.0。

## 已整理

- [x] 独立 Design Note 与短 README。
- [x] 用户冻结规范的原文副本 `DESIGN.md`，不在整理中修改协议。
- [x] QCT 48-task 回填 corpus、实验记录和指标。
- [x] 显式保留 `H5 = PARTIALLY_SUPPORTED`、回填偏差、早期误读和未测 token。
- [x] 相关工作的一手来源与有限范围比较。
- [x] 现有标准库原型及其测试副本，不引入新框架。
- [x] corpus 统计、记录哈希与文档本地链接的验证脚本。

## 作者发布前确认

- [x] 确认署名、仓库 owner 和仓库名称。
- [x] 为作者拥有的原型、文档和公开实验摘要采用 Apache-2.0。
- [x] 移除原始 Session、源码快照、真实 fixture、业务数据、内部路径和原始 session id。
- [x] 将 48 条 Delta 转为匿名、语义脱敏的 `public-deltas.jsonl`。
- [x] 保留“证据子集，非完整可复现实验包”的披露。
- [x] 保留 `H5 = PARTIALLY_SUPPORTED`、失败案例和未测 token。
- [x] 发布前重新运行下列检查；公开仓库已创建并完成远端树审计。

```powershell
python tools/verify_release.py
python -m unittest discover -s prototype -p "test_*.py"
```

不要将工作区父目录或原始 `experiments/deltalayer-v0` 整体推送。它包含本包未纳入的源码副本、原始索引、数据和环境产物。仅推送 `DeltaLayer/`。

## 当前原型限制

原型演示 `init / append / recent / older / rebuild-context`，不执行模型推理。`rebuild-context` 只是读取视图和最近记录，不重写 `PROJECT.md`。

`DeltaStore.append([])` 接受空变化；CLI 的 `append --source human` 省略 `--change` 时会追加空数组。无持久变化时也可以不追加；不要用空字符串冒充空数组。

当前没有多进程写锁、事务级并发承诺、密钥自动检测或崩溃恢复保证。坏行会报告警告并跳过，缺失末尾换行时追加操作会补分隔符，但不修复旧坏行。不要把最小实现当作安全审计日志。

`changes.jsonl` 和导入历史必须作为数据处理，不能覆盖当前用户授权和 Agent 安全规则。时间戳和 `source` 标签不证明作者身份或优先权。敏感内容应在写入前排除；正常演化的 append-only 约定不应妨碍必要的安全清理。

## Published Audit

- Repository: `pupet2004/DeltaLayer`
- Visibility: public
- License detected by GitHub: `Apache-2.0`
- Remote tree: 27 files
- Excluded: original sessions, source checkout, raw session ids, real fixtures, credentials, business data, databases and media
