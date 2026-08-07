# 执行计划：问题跟踪 / PR 双向同步（F-015）

> 状态：进行中
> 目标 Feature：F-015

## 目标

让 Issue、PR、feature-list、完成记录之间自动同步：Issue 创建自动生成 feature，PR 自动关联并回写状态，合并后自动归档并关闭 Issue，全程不需要人工搬状态。

## 验收标准

1. `harness github sync` 能从 GitHub 重新计算台账期望状态，dry-run 输出待应用变更。
2. Issue opened 自动创建 feature、最小计划文件，并把 `Feature ID` 回写 Issue 正文。
3. PR opened 自动回写 `pushed`、`pr_url`、`pr_number`；PR merged 自动归档并关闭关联 Issue。
4. PR closed 未合并回退 `in_progress`；Issue closed 未合并置 `blocked`。
5. 重复事件幂等，机器字段以台账为准，标题冲突不静默覆盖。
6. `harness github sync --strict` 作为 CI 门禁，`github-sync` 进入 required checks。
7. 真实 Issue 验证自动创建、状态回写和自动归档闭环。

## 影响文件

- 新增 `harness/github_sync.py`、`tests/test_github_sync.py`、`.github/workflows/issue-pr-sync.yml`
- 修改 `harness/cli.py`、`harness/git_ops.py`、`harness/check.py`、`.github/workflows/ci.yml`、`.harness/dod.json`
- 更新 feature-list schema 1.3、模板、Git 规则、AGENTS.d、`.harness/README.md`

## 验证入口

```bash
python -m pytest -q
python -m ruff check .
python -m harness check
python -m harness github sync --strict
python -m harness knowledge check
```
