# Codex 桌面版多智能体流水线流程

## 定位

本流程是可执行多智能体流水线的编排入口。协调者按 `.harness/pipelines/desktop-pipeline.json` 推进阶段，只做监督、门禁和汇报，不写业务代码。

## 启动

1. 读 `AGENTS.md`、`.harness/PROGRESS.md`、`.harness/changes/active/feature-list.json` 和对应 feature plan。
2. 读 `.harness/pipelines/desktop-pipeline.json`，确认阶段、依赖、门禁、重试上限。
3. 检查 `.harness/state/pipeline-desktop-<feature>.json`：
   - 不存在：按 `.harness/templates/pipeline-state.example.json` 的 schema 初始化。
   - 存在：恢复状态，从 `current_stage` 继续。

## 状态与文件

- 状态文件：`.harness/state/pipeline-desktop-<feature>.json`
- 阶段交接：`.harness/state/tasks/<feature>-<stage>.md`，必须使用 `.harness/templates/pipeline-handoff.md.template`
- 交接示例：`.harness/templates/pipeline-handoff.example.md`
- 阶段日志：`.harness/state/logs/<feature>-<stage>.log`
- 最终报告：`.harness/state/reports/pipeline-desktop-<feature>.md`

状态取值：

- 流水线：`not_started` / `running` / `blocked` / `done`
- 阶段：`queued` / `running` / `passed` / `failed` / `skipped`

## 执行规则

1. 按 `depends_on` 推进阶段；v1 为串行依赖，不启动并行。
2. 每个阶段依次执行：
   1. 创建任务卡，写入 scope、阶段目标、门禁、handoff 路径。
   2. 读取对应角色契约（`.harness/agents/pipeline/<role>.md`）。
   3. 执行阶段 Agent：优先使用 Codex 桌面版多智能体/子任务机制；不可用时由协调者按角色契约代理执行，但必须独立写 handoff。
   4. 校验 handoff：文件存在、`conclusion` 合法、必需字段完整；`review` 阶段额外校验 `review_verdict` 为 `pass` / `rework` / `needs_owner`。
   5. 运行门禁命令并记录退出码。
   6. 追加 journal，更新阶段状态。
3. 门禁失败：
   - `attempts + 1`，未达 `max_attempts` 时重试。
   - 达到上限后标记 `blocked`，升级 Owner。
4. escalation：
   - `blocking=true`：停止流水线，标记 `blocked`，问 Owner。
   - `blocking=false`：记入 journal，按 `default_if_ignored` 继续。
5. 评审打回：
   - `review` verdict 为 `rework` 时，`review.rework_count + 1`。
   - 未超过 `max_rework`：把 reviewer 问题清单作为 `rework_scope` 交回 `coding`。
   - 超过 `max_rework`：标记 `blocked`，升级 Owner。

## 门禁矩阵

| 阶段 | 默认门禁 |
| --- | --- |
| analysis | `script/check.ps1` |
| coding | `script/check.ps1 -Compile` |
| test | `script/check.ps1 -Backend` |
| review | `script/check.ps1` |

协调者可按实际影响面选择更轻的门禁，但必须在 journal 中记录原因。

## 收尾

全部阶段通过后：

1. 更新状态文件为 `done`。
2. 按 `.harness/templates/pipeline-report.md.template` 生成最终报告。
3. 回写 feature-list：`pipeline.status=done`、feature `status=ready_for_review`、追加 history。
4. 不自动 push；用户确认后执行 `harness commit -Feature <id>`、`harness push -Feature <id>`、`harness pr -Feature <id>`。
