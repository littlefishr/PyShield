# PyShield — 文件完整性监控练习 🛡️

项目为一个小型的文件完整性监控（File Integrity Monitor）工具，使用 SHA-256 哈希生成基线并检测后续文件变化。该项目适合作为信息安全与软件工程学习练习：实现文件哈希、基线管理、变更检测与 CLI 输出美化。

**主要特点**

- ✅ 基于 SHA-256 计算文件摘要
- ✅ 生成/读取 JSON 格式的基线文件
- ✅ 检测文件被修改、删除或新增（modified / deleted / added）
- ✅ 提供命令行入口（`main.py`），并用 `rich` 美化输出
- ✅ 易于测试：包含 pytest 用例，使用 `tmp_path` 保证隔离

**安装**

建议在虚拟环境中安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

如果你没有 `requirements.txt`，可以手动安装主要依赖：

```bash
pip install rich pytest
```

（本项目仅依赖标准库 + `rich` 用于终端展示，`pytest` 用于运行测试。）

**使用方法**

在仓库根目录下有一个 CLI 入口 `main.py`：

- 创建基线（Baseline）：扫描目录并将哈希写入基线文件

```bash
python3 main.py --action baseline --path . --output baseline.json
```

- 检查当前状态相对于基线的差异：

```bash
python3 main.py --action check --path . --output baseline.json
```

示例说明：

- `--path`：要监控的目录，默认当前目录 `.`。你可以指定单独的目录，例如 `src`。
- `--action`：`baseline` 或 `check`，默认 `check`。
- `--output`：基线文件路径，默认 `baseline.json`。

当基线不存在或无法解析时，工具会把当前所有文件视为新增（`added`）。建议先运行 `baseline` 创建初始基线，再使用 `check` 来检测后续变更。

**运行测试** 🧪

项目包含 pytest 测试，使用 `tmp_path` 做隔离。运行：

```bash
pytest -q
```

**学习项目** 📚

- 实践文件完整性监控的核心思想与实现（哈希计算、基线/比较逻辑）。
- 学习如何写可测试、可复现的代码（使用 `tmp_path` 的单元测试）。
- 练习构建简单且友好的 CLI 工具，并使用 `rich` 改善终端展示体验。
- 可延展为更完整的监控系统：支持定时扫描、签名/校验、远程基线存储或与 SIEM 集成。

---

