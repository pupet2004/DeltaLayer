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

## 向前读取

`recent` 返回 `next_before`。把返回的完整游标传给 `older --before`；游标包含时间与物理行号，同时间记录不会因分页而漏掉。

```powershell
$page = python prototype/deltalayer.py --root ./demo-project recent --limit 1 | ConvertFrom-Json
if ($page.next_before) {
    python prototype/deltalayer.py --root ./demo-project older --before $page.next_before --limit 5
}
```

模型决定是否继续回溯，CLI 不替模型判断是否理解足够。`rebuild-context` 只打包既有视图、最近记录及游标，不调用模型，也不重写 `PROJECT.md`。

## 边界

- 读取会扫描并排序完整本地文件，只把选中页返回给 Agent；没有大规模性能保证。
- 保持历史只追加。时间戳是记录信息，不证明因果或权限。
- 使用单写入者；没有多进程协调、事务级崩溃恢复或防篡改保证。
- 坏 JSON / UTF-8 行会被警告并跳过，不会自动修复。追加时会分隔缺失换行的末行，同时保留旧字节。
- 当前视图准确性和 change 语义质量由 Agent 与使用者负责。它不是自动接入所有 Agent 的插件。

本次整理运行 **14 项单元测试，全部通过**，覆盖字节保留、空变化、非法输入、坏行、断尾、同时间游标、时区顺序、CLI 与 2,500 条记录分页。这证明的是机械行为，不是 H5 的总成本假设。
