# 目录与知识索引

## 常用入口

- Harness 总览：`.harness/README.md`
- 进度状态：`.harness/PROGRESS.md` + `.harness/changes/active/feature-list.json`
- 规则：`.harness/rules/`
- 技能：`.harness/skills/`
- 技能路由：`request-analysis` / `coding-skill` / `frontend-backend-integration` / `expert-reviewer` / `unit-test-ci` / `db-schema-sync` / `deploy-verify`，详见 `.harness/skills/README.md`
- 变更与 Git 协作：`.harness/changes/` + `.harness/rules/git-workflow.md` + `script/sync-changes.ps1`
- 多智能体流水线：`.harness/pipelines/desktop-pipeline.json` + `.harness/agents/pipeline/` + `.harness/pipelines/desktop-coordinator.md`
- 项目知识：`.harness/wiki/`（初始化新项目时按需补充）
- 归档：`.harness/archive/harness-cli/`

## AI 自动加载范围

自动加载（进入 AI 上下文）：
- 根 `AGENTS.md` 和本目录（`AGENTS.d/`）导入文件；
- `.codex/skills/` 技能（任务匹配时自动发现）；
- `.codex/config.toml`（Codex 工具读取，不进入对话）。

按需读取（不自动加载）：
- `.harness/rules/`、`changes/`、`templates/`、`agents/`、`archive/`；
- `script/`、`harness-template/`、`benchmark/`。

维护规则：
- 自动加载内容保持精简，不放密钥、账号等敏感信息；
- 规则、知识、变更记录按需读取，不写入自动加载入口；
- 加载边界变化时同步更新本文件和 `.harness/README.md`。

## 按需读取判定

按需读取不是“可读可不读”，而是“命中触发条件必须读，未命中不读”。判断依据是：这份内容是否影响“能不能做、怎么做、做对没有”。

| 内容 | 必须读取的触发条件 |
| --- | --- |
| `rules/tool-access.md` | 要执行命令、编辑/删除文件、移动目录、发布或涉及权限前 |
| `rules/git-workflow.md` | 要 commit、push、建 PR，或更新 feature-list 的 Git 字段前 |
| `rules/development-flow.md` | 接到新任务、判断复杂度 L1-L4、确定流程前 |
| `rules/project-structure.md`、`backend-module-boundary.md` | 确定改哪个模块、模块是否启用、是否可改架构层前 |
| `rules/coding-standard.md`、`comment-guardrail.md`、`comment-review-checklist.md` | 开始写代码或交付前检查注释前 |
| `rules/sql-and-migration.md` | 涉及 SQL、表结构、初始化数据、迁移或回滚前 |
| `rules/documentation-change-rule.md` | 要更新接口、枚举、前端对接或设计文档前 |
| `rules/requirement-alignment-rule.md` | 需求不清晰、L3/L4、设计纠偏、跨模块方案前 |
| `skills/<名称>/SKILL.md` | 任务命中该技能描述，进入对应执行步骤时 |
| `changes/active/feature-list.json` | 每个任务开始时和每次状态变化时（建议每次会话必读） |
| `changes/active/*.md` | 任务有对应执行计划，需要确认步骤和验收条件时 |
| `changes/completed/*`、`INDEX.md` | 参考历史实现、复用旧方案或归档前 |
| `changes/tech-debt-tracker.md` | 发现遗留问题、排期或判断是否登记技术债时 |
| `templates/*` | 新建计划、会话交接、commit、PR 时 |
| `agents/owner.md` | 需要审批、升级、确认负责人时 |
| `agents/pipeline/*` | 启动、推进或恢复多智能体流水线，或作为阶段 Agent 执行时 |
| `pipelines/desktop-pipeline.json`、`desktop-coordinator.md` | 启动、推进或恢复多智能体流水线前 |
| `templates/pipeline-handoff.md.template`、`pipeline-state.example.json` | 写阶段交接物或初始化/校验流水线状态前 |
| `state/README.md` | 读写流水线状态或查看 schema 前 |
| `archive/harness-cli/*` | 追述历史实现时，只读参考 |
| `script/*` | 需要校验、同步技能、初始化项目或安装 hooks 时 |

快速判断口诀：
- 任务关键词命中“接口 / SQL / 权限 / Git / 部署 / 文档”时，先读对应规则和技能；
- 任务涉及“能不能做”先读规则，涉及“怎么做”先读技能，涉及“做到哪”先读 changes，涉及“事实是什么”先读 wiki；
- 不确定先读 `.harness/README.md` 的知识坐标，再按上表定位；
- 读之前先确认文件存在，读取后把结论写进交付说明，不把关键规则只放在聊天记忆里。
