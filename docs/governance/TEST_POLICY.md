# 测试执行与临时产物治理规则

## 1. 默认测试入口

默认使用统一入口执行测试：

```bash
python -m tools.test_runner.run_tests
```

说明：

- 该入口会通过 `python -m pytest` 执行测试。
- 自动使用专用 `--basetemp` 临时目录，隔离 pytest 自身的临时工作区。
- `python -m tools.test_runner.run_tests` 负责提供并清理 `--basetemp`。
- 仓库根目录 / `tests/` 残留扫描由 `tests/conftest.py` 中的 pytest 会话级守卫统一执行，不在 runner 中重复实现一套扫描逻辑。

调试场景允许直接运行 `pytest`，例如：

```bash
python -m pytest tests/test_temp_artifact_policy.py -q
```

直接运行 `pytest` 只适用于窄范围调试；仓库残留守卫仍然生效，且不放宽本文件对临时产物策略的限制。

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
- 若会话开始前已存在上述残留目录：测试也应失败，避免“带污染状态继续跑测”。
- 例外：`.git`、`.venv`、`.mypy_cache`、`.ruff_cache`、`.pytest_cache`、`__pycache__` 不属于该规则目标。

### 2.3 测试代码静态规则

仓库测试默认只允许通过 `ManagedTempArtifacts` / `ManagedTempArtifactsTestCase` 创建和清理测试工作目录。

测试代码中禁止直接使用以下机制：

- `tmp_path` / `tmp_path_factory`
- `pytester` / `runpytest` / `runpytest_subprocess`
- `tempfile.gettempdir()` / `tempfile.mkdtemp()` / `TemporaryDirectory`
- `tempfile.NamedTemporaryFile()` / `tempfile.mkstemp()` / `tempfile.TemporaryFile()`
- 手写 `shutil.rmtree(...)` 清理测试目录
- 直接写入疑似仓库临时目录字面量，例如：

  - `Path("tmp...")` / `Path('_tmp...')` / `Path("temp...")`
  - `mkdir("tmp...")` / `os.mkdir("tmp...")`
  - `Path(__file__).parent / "tmp..."`

统一替代方案：

- `ManagedTempArtifacts` / `ManagedTempArtifactsTestCase`

不得直接使用 `tmp_path` / `tmp_path_factory` 作为仓库测试的常规临时目录机制；这样可以确保临时目录路径、清理行为和残留扫描都落在统一策略下。

受控例外仅限以下自测文件：

- `tests/test_temp_artifact_policy.py`
- `tests/doc_governor/test_temp_artifacts.py`

这些文件允许直接引用被禁止的 API 或模式，以验证策略本身和 helper 自身行为；但它们仍必须把测试沙箱放在仓库外，并在测试结束后自清理，不得在仓库根目录或 `tests/` 下遗留 `tmp/temp` 目录。

### 2.4 调试例外与保留策略

- 默认情况下，`ManagedTempArtifacts` 会在测试结束时自动清理其工作目录。
- 如需保留 `ManagedTempArtifacts` 产物用于调试，可设置 `AI_FOR_INTERVIEWER_KEEP_TEST_ARTIFACTS=1`。
- 如需显式指定保留目录，应设置 `AI_FOR_INTERVIEWER_TEST_TEMP_ROOT`，且该路径必须位于仓库根目录与 `tests/` 之外。
- `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1` 只用于一次性诊断；它会关闭仓库根目录 / `tests/` 残留守卫，不能作为日常测试、提交前验证或 CI 的默认做法。
- 即使在调试模式下，也不得把 `tmp_path` / `tmp_path_factory` 恢复为常规测试入口。

## 3. pytest 会话级守卫

- pytest 会话开始时必须先记录仓库根目录、`tests/` 以及受控 managed temp root 的目录快照。
- pytest 会话在结束时必须执行仓库残留扫描，并对比会话开始前后的目录变化。
- 若发现根目录或 `tests/` 下 `tmp/temp` 命名目录残留，测试会话应失败。
- 若发现会话开始前已存在残留目录，也应标记失败，避免“带污染状态继续跑测”。
- `python -m tools.test_runner.run_tests` 与直接 `python -m pytest ...` 都应经过这套守卫；两者差别只在于前者额外提供并清理 `--basetemp`。

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
