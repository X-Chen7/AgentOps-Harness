# 流水线状态目录

本目录存放 Codex 桌面版多智能体流水线的运行期状态，不提交 Git（见 `.gitignore`）。

## 文件布局

- `pipeline-desktop-<feature>.json`：流水线状态与 Journal
- `tasks/<feature>-<stage>.md`：阶段交接物
- `logs/<feature>-<stage>.log`：阶段日志与门禁输出
- `reports/pipeline-desktop-<feature>.md`：最终报告

## 状态 schema

顶层字段：

- `schema_version`：`1.0`
- `feature_id`：关联的 feature
- `status`：`not_started` / `running` / `blocked` / `done`
- `current_stage`：当前阶段 id 或 null
- `stages`：阶段数组
- `journal`：追加式事件日志
- `created_at` / `updated_at`

阶段字段：

- `id`、`status`（`queued` / `running` / `passed` / `failed` / `skipped`）
- `attempts`、`max_attempts`、`rework_count`、`depends_on`
- `gate`、`started_at`、`finished_at`、`handoff`、`artifacts`、`last_error`

## 维护规则

- 状态文件由协调者更新，阶段 Agent 不直接改状态。
- 每个事件只追加到 journal，不覆盖历史。
- 运行中的状态不手改；必须修改时先记录原因。
- 状态示例见 `.harness/templates/pipeline-state.example.json`，交接示例见 `.harness/templates/pipeline-handoff.example.md`。
