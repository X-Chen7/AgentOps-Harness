# 执行计划：CI/CD 机器验收 + PR 门禁（F-012）

> 状态：进行中
> 目标 Feature：F-012

## 目标

把质量验收从“人记得在本地跑 check”升级为机器强制门禁：GitHub Actions 自动跑全部检查，PR 不满足 DoD 不能合入，本地通过 pre-commit / pre-push 提前拦截低级问题。

## 验收标准

1. `harness lint` 通过 ruff 检查与格式检查。
2. `pytest` 全部通过。
3. `harness check --ci` 在干净 checkout 下 0 error、0 warning。
4. `harness dod` 能校验 PR 标题与 body 必需段落。
5. `harness install-hooks` 支持 pre-commit 与 legacy 两种模式。
6. GitHub Actions 的 lint / test / dod / sql / backend 五个检查全部通过。
7. main 分支保护已开启，PR 未全绿不能合并。

## 影响文件

- 新增 `harness/lint.py`、`harness/sqlcheck.py`、`harness/dod.py`、`.pre-commit-config.yaml`、`.harness/dod.json`
- 修改 `harness/cli.py`、`harness/check.py`、`harness/hooks.py`、`.github/workflows/ci.yml`、`pyproject.toml`
- 新增测试 `tests/test_lint.py`、`tests/test_sqlcheck.py`、`tests/test_dod.py`

## 验证入口

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m harness check --ci
python -m harness dod
python -m harness lint
python -m harness check --sql
```
