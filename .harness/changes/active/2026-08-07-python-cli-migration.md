# 执行计划：PowerShell 工具链迁移到 Python CLI（F-011）

> 状态：进行中
> 目标 Feature：F-011

## 目标

将仓库的可执行工具链从 PowerShell 迁移为 Python CLI，改善求职仓库的语言画像，同时保持旧 PowerShell 入口完全兼容。

## 验收标准

1. `harness check` 与 `script/check.ps1` 行为一致，0 error。
2. `harness sync`、`sync-skills`、`init`、`install-hooks`、`commit/push/pr` 覆盖原脚本功能。
3. `pytest` 全部通过。
4. GitHub Actions CI 已配置。
5. README 与 Harness 文档说明新用法。

## 影响文件

- 新增 `harness/` Python 包、`pyproject.toml`、`tests/`、`.github/workflows/ci.yml`
- `script/*.ps1` 改为 Python CLI 薄包装
- `README.md`、`AGENTS.d/02-verification.md`、`.harness/README.md`、`harness-template/README.md`

## 验证入口

```bash
python -m pytest -q
python -m harness check
script/check.ps1
```
