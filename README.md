# AgentOps-Harness

可执行的多智能体协作治理体系（Harness Engineering）：把 AI 编码从“每次读文档”升级为“按流程执行、按门禁验收、按状态流转”的工程化流水线。支持个人、团队和 Agent 平台复用。

## 已落地能力

### 入口与状态

- `AGENTS.md` / `AGENTS.d/`：定义 AI 自动加载边界和按需读取判定。
- `.harness/PROGRESS.md` + `.harness/changes/active/feature-list.json`（schema 1.3）：机器可读状态权威，覆盖 feature 完整生命周期。

### 角色与多智能体流水线

- `.harness/agents/`：owner 与 analyst / coder / coordinator / reviewer / debater 角色契约。
- `desktop-pipeline.json`：串行 DAG 执行 `analysis -> coding -> test -> review -> Git/PR`，支持 `depends_on` 扩展并行。
- 写权仲裁、便签墙、debate 轻量版，降低多 Agent 并发写冲突。

### 规则、技能、变更与模板

- `.harness/rules/`：长期规则，包括 Git 工作流、修改边界、验收入口。
- `.harness/skills/`：8 个可执行技能，统一 `skill.yaml` 契约，可同步到 `.codex/skills/`。
- `.harness/changes/`：feature 计划、执行状态、完成索引。
- `.harness/templates/`：初始化、会话交接、PR、commit、pipeline 报告模板。

### Python CLI

- 统一命令：`harness check / sync / commit / push / pr / skill / knowledge / github`。
- PowerShell 兼容入口保留在 `script/`，旧脚本可继续使用。

### CI/CD 机器验收 + PR 门禁

- GitHub Actions 8 项 required checks：`lint / test / dod / sql / backend / skills / knowledge / github-sync`。
- `harness dod` 校验 PR 标题和正文；`harness check --ci/--sql` 覆盖结构、SQL 与后端。
- pre-commit / pre-push 在本地提前拦截。
- main 使用 repository ruleset：代码改动必须走 PR，机器验收不通过不能合入。

### 技能注册表 + 技能测试与评测

- `skill.yaml` 定义名称、触发条件、版本和依赖，`harness skill validate` 做 schema 校验。
- fixture 测试用“输入样例 -> 期望输出”验证技能行为。
- `harness skill bench --save / --compare` 提供 golden benchmark，技能改坏会被回归拦截。

### 知识库检索化

- `harness knowledge index` 生成结构化索引。
- `route / search / get / api / table` 支持任务路由、关键字召回、定点读片段、API 和表结构查询。
- 从 Java Controller 和 SQL 提取 API、表结构事实，降低手工维护成本。
- `harness knowledge check` 防过期、断链和缺失；`bench` 8 用例守住检索质量。

### 问题跟踪 / PR 双向同步

- GitHub 事件驱动：Issue 创建自动生成 feature 和计划；PR 打开自动回写 `pushed`；PR 合并自动归档、更新 `INDEX.md` / `PROGRESS.md`、重建 knowledge index、关闭关联 Issue。
- Issue 关闭未合并自动置 `blocked`；PR 关闭未合并自动回退。
- `harness github sync / issue-create` 提供 dry-run、apply、strict 三种模式，`--strict` 作为 CI 门禁。
- 配置 `HARNESS_SYNC_TOKEN` 后机器人直写 main；直写路径白名单只允许 `.harness/changes/**`、`.harness/PROGRESS.md`、`.harness/knowledge/**`。
- 未配置令牌时自动降级为“状态同步 PR + auto-merge”。

## 一次完整闭环

`Issue 创建` -> `自动生成 F-XXX feature/计划` -> `analysis -> coding -> test -> review` -> `PR` -> `8 项 CI 门禁` -> `合并` -> `自动归档并关闭 Issue`。全程状态只维护在 `feature-list.json`，GitHub Issue/PR 只是外部投影。

## 快速开始

```bash
pip install -e .
python -m harness --help

python -m harness check
python -m harness skill validate
python -m harness skill test
python -m harness skill bench --compare
python -m harness knowledge index
python -m harness knowledge route "接口 字段 规则"
python -m harness github sync --strict
```

Git 与 PR 流程：

```bash
python -m harness commit --feature F-009
python -m harness push --feature F-009
python -m harness pr --feature F-009
```

PowerShell 兼容入口：

```powershell
script/check.ps1
script/sync-skills.ps1
script/sync-changes.ps1 -PushGate
script/harness-git.ps1 commit -Feature F-009
```

## 初始化新项目

```bash
python -m harness init --target C:\path\to\new-project --project-name my-project
```

## 目录结构

```text
.harness/         治理体系：agents / rules / skills / changes / templates / knowledge / pipelines
.github/workflows/ CI 与 Issue/PR 自动同步
harness/          Python CLI 实现
tests/            pytest 测试
script/           PowerShell 兼容入口
```

## 验证基线

- pytest 82 passed
- `harness check` 0 errors
- `harness knowledge bench` 8/8
- `harness github sync --strict` up to date
- GitHub Actions 8 项 required checks 全绿

## 说明

本仓库是通用 AgentOps 治理框架的演示仓库，业务代码仅作示例，不包含任何特定公司的业务实现。
