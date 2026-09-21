# DeltaLayer v0 Prototype

发布包中的标准库原型。本文列出本包可执行的命令和边界。

## 试用

Python 3.10+。以下命令从 **DeltaLayer 仓库根目录** 执行，无需安装第三方依赖：

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python prototype/deltalayer.py --root ./demo-project init
python prototype/deltalayer.py --root ./demo-project append --source human --change "选择语义变化作为项目连续性实验入口"
python prototype/deltalayer.py --root ./demo-project append --source human
python prototype/deltalayer.py --root ./demo-project recent --limit 3
python prototype/deltalayer.py --root ./demo-project rebuild-context --limit 3
python -m unittest discover -s prototype -p "test_*.py" -v
```

不传 `--change` 会追加 `changes: []`，多项变化则重复传 `--change`。省略 `--time` 时使用带时区的运行时本地时间。

`init` 创建 `PROJECT.md` 和 `.deltalayer/changes.jsonl`，并在目标 `AGENTS.md` 追加一次带标记的行为约定；已有视图和历史不会被清空。完整示例见 [`examples/`](examples/)。

## 时间戳约定

`time` SHOULD use an offset-aware ISO 8601 timestamp whenever available.

例如 `2026-09-21T21:43:12+08:00`，或带 `Z` 的 UTC 时间。不要臆造缺失的时刻或时区，也不要补写旧记录。

`now_timestamp()` 仍自动生成本地 offset-aware 时间。原型兼容已有的 `YYYY-MM-DD` date-only 值，按日期解析，不转换成午夜或补造时区；返回值、游标和历史文件保留日期精度。显式 `--time` 也接受日期；包含具体时刻的 timestamp 仍须带时区，非法日期仍拒绝。

[Qicetai Case 2](../docs/native-dogfood-qicetai-20260921.md) 与 evidence 快照记录的是归档时会跳过末两条 date-only 的旧行为。兼容性修复后，原始九条记录均可读取并分页，没有警告；历史证据不随实现修复改写。

## 向前读取

单一 JSONL 的事件顺序由追加位置决定。`recent` 从文件末尾向前返回；即使时间倒退、重复或混合日期与完整 timestamp，也不按时间重排。

`recent` 返回 `next_before`。把完整游标传给 `older --before`；沿用已有的 `<time>#line=<物理行号>` 格式，以行号划定排他分页边界，不用缺失的具体时刻做比较。例如 `2026-09-21#line=8` 保留日期精度，下一页读取第 8 行之前的有效记录。

```powershell
$page = python prototype/deltalayer.py --root ./demo-project recent --limit 1 | ConvertFrom-Json
if ($page.next_before) {
    python prototype/deltalayer.py --root ./demo-project older --before $page.next_before --limit 5
}
```

模型决定是否继续回溯，CLI 不替模型判断是否理解足够。`rebuild-context` 只打包既有视图、最近记录及游标，不调用模型，也不重写 `PROJECT.md`。

旧式 `older --before <offset-aware timestamp>` 在历史全部为带时区 timestamp 时仍支持排他时间过滤，结果保持追加位置倒序；它不是完整游标分页。边界或历史中存在 date-only 时，该形式会明确报错并要求完整游标，避免猜测同日先后或默默遗漏记录。

## 边界

- 读取会扫描完整本地文件，按追加位置倒序选页返回给 Agent；没有大规模性能保证。
- 保持历史只追加。时间戳是记录信息，不证明因果或权限。
- 使用单写入者；没有多进程协调、事务级崩溃恢复或防篡改保证。
- 坏 JSON / UTF-8 行会被警告并跳过，不会自动修复。追加时会分隔缺失换行的末行，同时保留旧字节。
- 当前视图准确性和 change 语义质量由 Agent 与使用者负责。它不是自动接入所有 Agent 的插件。

本次兼容性修复运行 **21 项单元测试，全部通过**，覆盖字节保留、空变化、非法输入、坏行、断尾、重复日期、混合精度、时间倒退、翻页期间追加、CLI、context 打包与 2,500 条记录分页。这证明的是机械行为，不是 H5 的总成本假设。
