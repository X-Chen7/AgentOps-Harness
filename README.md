# AgentOps-Harness

AgentOps-Harness 是一个可执行的多智能体协作治理体系（Harness Engineering），把 AI 编码从“每次读文档”升级为“按流程执行、按门禁验收、按状态流转”的工程化流水线。

## 核心能力

- 入口与状态：`AGENTS.md`、`AGENTS.d/`、`.harness/PROGRESS.md`、`.harness/changes/active/feature-list.json`
- 角色与审批：`.harness/agents/owner.md`、`.harness/agents/pipeline/`
- 长期规则：`.harness/rules/`
- 可执行技能：`.harness/skills/`
- 变更与 Git 协作：`.harness/changes/`、`harness sync`、`harness commit/push/pr`
- 多智能体流水线：`.harness/pipelines/desktop-pipeline.json`、`.harness/agents/pipeline/`
- 模板与基准：`.harness/templates/`、`benchmark/`
- 初始化：`harness-template/`、`harness init`

## 快速使用

```bash
python -m harness check                  # Harness 与快速检查（推荐）
python -m harness check --backend        # 包含后端模块测试和打包
python -m harness sync-skills            # 同步技能到 .codex/skills
python -m harness sync --push-gate       # Git push 前门禁
python -m harness commit --feature F-009
python -m harness push --feature F-009
python -m harness pr --feature F-009
```

旧入口保持兼容，等价于上面的 Python 命令：

```powershell
script/check.ps1                  # Harness 与快速检查
script/sync-skills.ps1            # 同步技能到 .codex/skills
script/sync-changes.ps1 -PushGate # Git push 前门禁
script/harness-git.ps1 commit -Feature F-009
script/harness-git.ps1 push -Feature F-009
script/harness-git.ps1 pr -Feature F-009
```

## 安装 CLI

```bash
pip install -e .
python -m harness --help
```

安装后若 Python 的 `Scripts` 目录已在 PATH 中，也可以直接使用 `harness --help`。

初始化到新项目：

```bash
python -m harness init --target C:\path\to\new-project --project-name my-project
```

或使用兼容入口：

```powershell
powershell -ExecutionPolicy Bypass -File script\harness-init.ps1 -Target C:\path\to\new-project -ProjectName my-project
```

## 演示流水线

F-009 是一个端到端演示 feature：为 `harness check` 增加流水线终态一致性校验，并完整跑通 `analysis -> coding -> test -> review -> Git/PR`。

## 说明

本仓库是通用 AgentOps 治理框架的演示仓库，业务代码仅作为示例，不包含任何特定公司的业务实现。
