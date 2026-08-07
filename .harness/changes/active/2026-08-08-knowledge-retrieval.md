# 执行计划：知识库检索化（F-014）

> 状态：进行中
> 目标 Feature：F-014

## 目标

把知识库从“Markdown 全文按需读”升级为“机器可读索引 + 结构化事实 + 定点检索”，降低 token、减少幻觉、防止知识过期，并让检索质量可被基准验证。

## 验收标准

1. `harness knowledge index` 生成 `.harness/knowledge/index.json`，覆盖 rules、wiki、skills、AGENTS、状态和结构化事实。
2. `harness knowledge route / search / get / api / table` 全部可用且确定性排序。
3. `harness knowledge check` 能拦截索引缺失、过期、断链、覆盖缺失和结构化条目不同步。
4. `harness knowledge bench --save / --compare` 8 个检索用例全过，且能检测回归和删用例。
5. GitHub Actions 新增 `knowledge` job，并纳入 `.harness/dod.json` required_checks 和 main 分支保护。
6. ruoyi 真实项目验证：索引 783 条目、接口事实 147 个、表结构事实 89 张，`platform_core_org` 等真实查询命中。

## 影响文件

- 新增 `harness/knowledge.py`、`tests/test_knowledge.py`、`.harness/knowledge/`、`.harness/benchmarks/knowledge/`
- 修改 `harness/cli.py`、`harness/check.py`、`harness/init_project.py`、`.github/workflows/ci.yml`、`.harness/dod.json`
- 更新 `AGENTS.d/00-common.md`、`.harness/README.md`、README、harness-template、benchmark 说明

## 验证入口

```bash
python -m pytest -q
python -m ruff check .
python -m harness knowledge index
python -m harness knowledge check
python -m harness knowledge bench --compare
python -m harness check
```
