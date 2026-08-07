# .harness 工程治理体系

本目录是项目的 Harness Engineering 规则、技能、变更记录和知识库。

## 入口

智能体入口是仓库根目录的 `AGENTS.md`；完整目录地图和知识坐标见下文。

## 五子系统落地

| 子系统 | 落地物 |
| --- | --- |
| 指令 | `AGENTS.md` + `.harness/rules/` |
| 工具 | `.harness/rules/tool-access.md` |
| 环境 | `.harness/init-contract.md` + `.harness/wiki/README.md` |
| 状态 | `.harness/PROGRESS.md` + `.harness/changes/active/feature-list.json` |
| 反馈 | `harness check` + `.harness/skills/unit-test-ci/SKILL.md` |

## 五支柱

| 目录 | 职责 |
| --- | --- |
| `agents/` | 角色、审批矩阵、风险升级路径 |
| `rules/` | 长期开发规则和边界 |
| `skills/` | 可执行的智能体技能，`SKILL.md` 为唯一权威 |
| `changes/` | 执行中计划、功能清单、完成记录、技术债 |
| `wiki/` | 项目事实、API、数据模型、前端对接和设计说明 |

## 辅助目录

| 路径 | 用途 |
| --- | --- |
| `templates/` | 初始化契约、会话交接、PROGRESS、feature-list、commit、PR 模板 |
| `pipelines/` | 多智能体流水线定义与流程提示词 |
| `state/` | 桌面版流水线运行期状态（不提交 Git） |
| `archive/harness-cli/` | harness-cli v1 运行器与流水线配置归档，只读 |

## 示例项目目录地图

Harness 可初始化到任意后端工程。参考目录：

| 目录 | 职责 |
| --- | --- |
| `app-framework/` | 框架 Starter、公共能力、横切能力 |
| `app-server/` | 服务启动入口、模块装配、运行配置、打包 |
| `app-module-*/` | 后端业务模块 |
| `sql/` | 数据库结构、初始化数据、修复脚本 |
| `script/` | 辅助脚本、部署脚本、运维脚本 |
| `.harness/` | Harness Engineering 智能体知识体系 |

## Harness 知识坐标

| 目标 | 位置 |
| --- | --- |
| 进度状态 | `.harness/PROGRESS.md` |
| 初始化契约 | `.harness/init-contract.md` |
| 角色和职责 | `.harness/agents/owner.md` |
| 工具边界 | `.harness/rules/tool-access.md` |
| 工程结构规则 | `.harness/rules/project-structure.md` |
| 编码规范 | `.harness/rules/coding-standard.md` |
| 注释防遗漏机制 | `.harness/rules/comment-guardrail.md` |
| 注释检查清单 | `.harness/rules/comment-review-checklist.md` |
| 开发流程 | `.harness/rules/development-flow.md` |
| Git 协作规则 | `.harness/rules/git-workflow.md` |
| 模块边界 | `.harness/rules/backend-module-boundary.md` |
| SQL 和迁移规则 | `.harness/rules/sql-and-migration.md` |
| 文档变更规则 | `.harness/rules/documentation-change-rule.md` |
| 需求对齐和设计纠偏规则 | `.harness/rules/requirement-alignment-rule.md` |
| 需求分析技能 | `.harness/skills/request-analysis/SKILL.md` |
| 编码实现技能 | `.harness/skills/coding-skill/SKILL.md` |
| 前后端对接技能 | `.harness/skills/frontend-backend-integration/SKILL.md` |
| 专家评审技能 | `.harness/skills/expert-reviewer/SKILL.md` |
| 单元测试编写技能 | `.harness/skills/unit-test-write/SKILL.md` |
| CI 验证技能 | `.harness/skills/unit-test-ci/SKILL.md` |
| 数据模型同步技能 | `.harness/skills/db-schema-sync/SKILL.md` |
| 部署验证技能 | `.harness/skills/deploy-verify/SKILL.md` |
| 项目知识 | `.harness/wiki/README.md` |
| 知识检索索引 | `.harness/knowledge/` + `harness knowledge index` |
| 知识定点检索 | `harness knowledge route/search/get` |
| 接口事实 | `.harness/knowledge/api/` + `harness knowledge api <路径>` |
| 表结构事实 | `.harness/knowledge/schema/` + `harness knowledge table <表名>` |
| 知识检索基准 | `.harness/benchmarks/knowledge/` + `harness knowledge bench` |
| 当前执行计划 | `.harness/changes/active/` |
| 功能状态机 | `.harness/changes/active/feature-list.json` |
| 已完成记录 | `.harness/changes/completed/` |
| 完成记录索引 | `.harness/changes/completed/INDEX.md` |
| 技术债 | `.harness/changes/tech-debt-tracker.md` |
| changes 同步脚本 | `harness sync`（兼容 `script/sync-changes.ps1`） |
| pre-push hooks 安装 | `harness install-hooks`（兼容 `script/install-hooks.ps1`） |
| Codex 项目配置 | `.codex/config.toml` + `.codex/README.md` |
| Codex 技能同步 | `.codex/skills/` + `harness sync-skills`（兼容 `script/sync-skills.ps1`） |
| AI 自动加载范围 | `AGENTS.d/00-common.md` + 本文件 |
| Harness 初始化模板 | `harness-template/` + `harness init`（兼容 `script/harness-init.ps1`） |
| Harness 基准测试 | `benchmark/README.md` |
| 桌面版多智能体角色 | `.harness/agents/pipeline/`（协调者 + 分析/编码/测试/评审） |
| 桌面版流水线配置 | `.harness/pipelines/desktop-pipeline.json` |
| 桌面版流水线流程 | `.harness/pipelines/desktop-coordinator.md` |
| 阶段交接协议 | `.harness/templates/pipeline-handoff.md.template` |
| 流水线状态 schema | `.harness/state/README.md` + `.harness/templates/pipeline-state.example.json` |
| 流水线状态 | `.harness/state/` + feature-list 的 `pipeline` 字段 |
| Git/PR 自动化 | `harness commit/push/pr` + `harness install-hooks`（兼容 `script/harness-git.ps1`、`script/install-hooks.ps1`） |
| Issue/PR 双向同步 | `harness github sync` + `.github/workflows/issue-pr-sync.yml` |
| 状态同步门禁 | `harness github sync --strict`（CI `github-sync` job） |
| 已退役执行器 | `.harness/archive/harness-cli/`（harness-cli v1 归档，只读） |

## 维护规则

- 每个事实只在一个权威文件维护，其它位置只做链接。
- live 目录不保留 `*-spec.md` 草案。
- `skills/` 保持一级平铺目录。
- `changes/active/` 只放未完成计划，WIP=1：同一时间只允许一个 `in_progress`。
- 功能状态以 `changes/active/feature-list.json` 为机器可读权威。
- feature 状态与 Git 绑定：committed / pushed / merged 必须回写 commit、branch、push_status；规则见 `.harness/rules/git-workflow.md`。
- 完成记录必须同步维护 `changes/completed/INDEX.md`。
- 桌面版流水线运行后必须由协调者同步 feature-list 的 `pipeline` 字段；`.harness/state/` 是运行期事实，不手改运行中的状态。
- 自动加载范围以 `AGENTS.d/00-common.md` 为准，保持入口精简，敏感信息不进入自动加载内容。
- 每次会话结束更新 `PROGRESS.md`，运行 `harness check`（或兼容的 `script/check.ps1`）并回填结果。
- 完成判定必须经过验证命令和 `expert-reviewer`，不能由执行者自报完成。
- 知识库索引必须用 `harness knowledge index` 重建，禁止手改 `index.json`；`harness check` 会强制校验索引新鲜度、覆盖率和断链。
- Issue/PR 状态以 `feature-list.json` 为权威，GitHub 事件只触发重新计算，不直接改写台账。

## 参考

- 参考开源约定：`AGENTS.md` 作为统一入口、技能目录平铺、每个技能 `SKILL.md` 自包含、状态外部化、完成判定独立化。
- 本项目的 `rules/`、`skills/`、`changes/`、`wiki/` 保留通用治理语义，不照搬外部工具链。
