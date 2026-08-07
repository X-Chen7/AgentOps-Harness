# 执行计划：技能注册表 + 技能测试与评测（F-013）

> 状态：进行中
> 目标 Feature：F-013

## 目标

把技能从“Markdown 文档 + 文件一致性校验”升级为“机器可读契约 + 场景测试 + 基线回归 + 真实反馈回流”，让技能改动是否变坏变得可验证。

## 验收标准

1. 8 个技能目录都提供 `skill.yaml`，`harness skill validate` 0 error。
2. `harness skill test` 能运行自动化 fixtures，并区分 manual fixture。
3. `harness skill bench --save / --compare` 能保存基线并检测回归。
4. `harness skill record / promote` 能记录真实执行反馈并生成 fixture 骨架。
5. `sync-skills` 不把 fixtures 和 feedback 文件安装到 `.codex/skills`。
6. GitHub Actions 新增 `skills` job 并纳入 required checks。

## 影响文件

- 新增 `harness/skill_contract.py`、`harness/skill_test.py`、`harness/skill_bench.py`、`harness/skill_feedback.py`
- 修改 `harness/cli.py`、`harness/skills.py`、`pyproject.toml`、`.github/workflows/ci.yml`、`.harness/dod.json`
- 新增 8 个 `skill.yaml`、4 个 fixture 用例及测试文件

## 验证入口

```bash
python -m pytest -q
python -m harness skill validate
python -m harness skill test
python -m harness skill bench --compare
python -m harness check
```
