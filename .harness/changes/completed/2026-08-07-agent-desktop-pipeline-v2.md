# Codex 桌面版可执行多智能体流水线 v2 完成记录

## 1. 完成摘要

- 完成日期：2026-08-07
- 执行人：Harness 维护
- 关联计划：`changes/completed/archive/2026-08-07-agent-desktop-pipeline-v2.md`
- 关联 commit：本次 F-008 提交（`git log -1` 可查）
- 关联 PR：未记录
- 当前结论：F-008 已落地，流水线从“角色文档 + 串行提示词”升级为“可校验的契约 + 状态机 + 交接协议 + 门禁/重试/打回/升级语义”。

## 2. 实际改动

| 文件 | 改动 |
| --- | --- |
| `.harness/pipelines/desktop-pipeline.json` | 新增：4 阶段、依赖、门禁、重试上限、max_rework |
| `.harness/templates/pipeline-handoff.md.template` | 新增：阶段交接协议 |
| `.harness/templates/pipeline-handoff.example.md` | 新增：交接物示例 |
| `.harness/templates/pipeline-state.example.json` | 新增：状态 schema 示例 |
| `.harness/state/README.md` | 更新：状态目录和 schema 说明 |
| `.harness/agents/pipeline/*.md` | 更新：角色契约加入 handoff、escalation、重试/打回语义 |
| `.harness/pipelines/desktop-coordinator.md` | 更新：CEO/PM 编排流程、门禁矩阵、收尾规则 |
| `.harness/templates/pipeline-task-card.md.template` | 更新：任务卡加入 handoff 路径和协作约束 |
| `.harness/templates/pipeline-report.md.template` | 更新：报告加入阶段表、Journal、证据、风险 |
| `script/harness-check.ps1` | 扩展：校验流水线配置、状态 schema、模板、依赖环、门禁文件 |
| `AGENTS.d/00-common.md` | 更新：多智能体流水线按需读取判定 |
| `.harness/README.md` | 更新：流水线配置、交接协议、状态 schema 知识坐标 |
| `.harness/PROGRESS.md`、`feature-list.json` | 登记 F-008 并标记完成 |

## 3. 功能能力

- 四个阶段：`analysis -> coding -> test -> review`，由协调者统一推进。
- 状态机：流水线 `not_started / running / blocked / done`，阶段 `queued / running / passed / failed / skipped`。
- 交接协议：每个阶段写固定 handoff，产物经 handoff 和 artifacts 注入下一阶段。
- 门禁与重试：每阶段按配置跑门禁，未达 `max_attempts` 可重试，超限标记 `blocked`。
- 评审打回：`review` 输出 `rework` 时携带问题清单回到 `coding`，最多 `max_rework` 轮。
- 升级通道：handoff 的 `escalations` 支持 `normal / scope / dep`，`blocking=true` 暂停流水线。
- 可观测性：状态 JSON 是追加式 Journal，配合阶段日志和最终报告。
- Git/PR：完成后不自动 push，由 `script/harness-git.ps1` 在用户确认后执行。

## 4. 验证结果

| 验证项 | 结果 |
| --- | --- |
| PowerShell 语法 | `harness-check.ps1`、`harness-git.ps1` 0 error |
| JSON 解析 | pipeline 配置、状态示例、feature-list 全部可解析 |
| `script/check.ps1` | 0 error，仅大文档 warning |
| `script/sync-changes.ps1` | 0 error |
| `git diff --check` | 0 |
| 负向验证 | 非法状态文件被 `harness-check` 拦截并报错 |

## 5. 审计发现的不足与修复

| 不足 | 修复 |
| --- | --- |
| 无统一状态 schema | 新增 `pipeline-state.example.json` 和 state README 说明 |
| 无阶段交接协议 | 新增 handoff 模板与示例 |
| 门禁/重试/升级规则分散 | 收敛到 pipeline 配置、协调者流程和角色契约 |
| `harness-check` 不校验桌面流水线 | 扩展配置、状态、模板、依赖环、门禁文件校验 |
| 模板占位符不完整 | 修复 `conclusion` 等占位符 |
| 阶段 Agent 如何执行不明确 | 协调者文档写明优先子任务机制，缺失时代理执行并写独立 handoff |
| 知识索引缺失 | 更新 `AGENTS.d/00-common.md` 和 `.harness/README.md` |

## 6. 遗留风险与下一步

| 风险/事项 | 建议处理 |
| --- | --- |
| 尚未用真实 feature 完整跑一遍 | 用 F-001 或新 L1 feature 走一次端到端流水线 |
| 仓库无 remote | 配置 origin 后验证 push/PR |
| state 运行产物不提交 Git | 需要跨设备共享时改用 feature-list 或 CI 持久化 |
| `-Backend` 门禁较慢 | 按实际影响面选择更轻门禁并在 journal 记录原因 |
