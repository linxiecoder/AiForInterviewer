---
title: TEST_POLICY
type: governance
status: active-f0
owner: 测试治理
permalink: ai-for-interviewer/docs/00-governance/test-policy
---

# TEST_POLICY

本文档定义当前测试临时产物治理规则。当前有效入口以 `docs/00-governance/DOCS_INDEX.md` 为准；旧路径 `docs/governance/**` 不作为 active 治理入口。

## 1. 测试临时产物策略

- 测试优先使用 `ManagedTempArtifacts` / `ManagedTempArtifactsTestCase` 管理项目自建临时目录。
- 测试不得直接调用 `tempfile.gettempdir()`、`tempfile.mkdtemp()`、`TemporaryDirectory()`、`NamedTemporaryFile()`、`mkstemp()` 或 `TemporaryFile()`。
- 允许使用 pytest 受管临时夹具，如 `tmp_path`、`tmp_path_factory`、`pytester` 和 `runpytest` 类 helper；使用边界必须是 pytest 在仓库根目录外创建和清理的临时目录，不得持久化为仓库内测试产物。
- 测试不得在仓库根目录或 `tests/` 下直接创建 `_tmp`、`tmp`、`temp` 或其变体目录。
- 测试不得手写 `shutil.rmtree()` 清理测试目录，应交由受管临时产物工具完成。

## 2. 环境变量

| 变量 | 用途 |
| --- | --- |
| `AI_FOR_INTERVIEWER_TEST_TEMP_ROOT` | 覆盖受管测试临时产物根目录 |
| `AI_FOR_INTERVIEWER_KEEP_TEST_ARTIFACTS` | 调试时保留受管测试产物 |
| `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS` | 调试时临时放宽仓库测试目录残留检查 |

## 3. 策略验证

- `tests/test_temp_artifact_policy.py` 负责扫描测试代码中的禁止临时目录模式，并验证本文档仍描述 pytest 受管夹具例外与 repo-root 临时产物禁止边界。
- `tests/doc_governor/test_temp_artifacts.py` 负责验证 `ManagedTempArtifacts` 和 `ManagedTempArtifactsTestCase` 的行为。
