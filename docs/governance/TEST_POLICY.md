# 测试执行与临时产物治理规则

## 1. 默认测试入口

默认使用统一入口执行测试：

```bash
python -m tools.test_runner.run_tests
```

说明：

- 该入口会通过 `python -m pytest` 执行测试。
- 自动使用专用 `--basetemp` 临时目录。
- 测试结束后自动清理该临时目录。

调试场景允许直接运行 `pytest`，例如：

```bash
python -m pytest tests/test_temp_artifact_policy.py -q
```

## 2. 临时产物硬规则

### 2.1 目录命名规则

临时目录命名匹配正则：

```text
^(?:_?tmp|temp)(?:[-_].*)?$
```

覆盖示例：

- `tmp`
- `_tmp`
- `temp`
- `tmp-xxx`
- `tmp_xxx`
- `_tmp-xxx`
- `_tmp_xxx`
- `temp-xxx`
- `temp_xxx`

### 2.2 仓库残留规则

- 仓库根目录出现上述 `tmp/temp` 目录：测试应失败。
- `tests/` 目录（含递归子目录）出现上述 `tmp/temp` 目录：测试应失败。
- 例外：`.git`、`.venv`、`.mypy_cache`、`.ruff_cache`、`.pytest_cache`、`__pycache__` 不属于该规则目标。

### 2.3 测试代码静态规则

测试代码中禁止直接写入疑似仓库临时目录字面量，例如：

- `Path("tmp...")` / `Path('_tmp...')` / `Path("temp...")`
- `mkdir("tmp...")` / `os.mkdir("tmp...")`
- `Path(__file__).parent / "tmp..."`

请改用：

- `ManagedTempArtifacts` / `ManagedTempArtifactsTestCase`
- 或 pytest 提供的 `tmp_path` / `tmp_path_factory`

## 3. pytest 会话级守卫

- pytest 会话在结束时必须执行仓库残留扫描。
- 若发现根目录或 `tests/` 下 `tmp/temp` 命名目录残留，测试会话应失败。
- 若会话开始前已存在残留目录，也应标记失败，避免“带污染状态继续跑测”。

## 4. pre-commit / pre-push / CI 建议

当前仓库未自动启用 `.pre-commit-config.yaml`。建议后续接入以下检查：

```yaml
repos:
  - repo: local
    hooks:
      - id: unit-temp-artifact-policy
        name: unit-temp-artifact-policy
        entry: python -m unittest tests.test_temp_artifact_policy -v
        language: system
        pass_filenames: false
      - id: unit-basic-memory-guard
        name: unit-basic-memory-guard
        entry: python -m unittest tests.basic_memory_guard.test_guard -v
        language: system
        pass_filenames: false
```

CI / pre-push 最低建议命令：

```bash
python -m unittest tests.test_temp_artifact_policy -v
python -m unittest tests.basic_memory_guard.test_guard -v
python -m tools.test_runner.run_tests
```

## 5. Codex 收口必做验证

当任务涉及测试、治理脚本或临时目录处理时，收口前至少执行：

```bash
python -m unittest tests.test_temp_artifact_policy -v
python -m unittest tests.basic_memory_guard.test_guard -v
```

并进行残留扫描：

```powershell
$pattern = '^(?:_?tmp|temp)(?:[-_].*)?$'

Get-ChildItem -Path . -Directory -Force |
  Where-Object { $_.Name -match $pattern } |
  Select-Object FullName, Name

Get-ChildItem -Path tests -Directory -Recurse -Force |
  Where-Object { $_.Name -match $pattern } |
  Select-Object FullName, Name
```

