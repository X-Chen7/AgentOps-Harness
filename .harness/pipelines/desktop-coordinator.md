# Codex 桌面版多智能体流水线流程

## 定位

本流程是可执行多智能体流水线的编排入口。协调者按 `.harness/pipelines/desktop-pipeline.json` 推进阶段，只做监督、门禁、写权仲裁和汇报，不写业务代码。

## 启动

1. 读 `AGENTS.md`、`.harness/PROGRESS.md`、`.harness/changes/active/feature-list.json` 和对应 feature plan。
2. 读 `.harness/pipelines/desktop-pipeline.json`，确认阶段、依赖、门禁、重试上限和 `write_scope`。
3. 检查 `.harness/state/pipeline-desktop-<feature>.json`：
   - 不存在：按 `.harness/templates/pipeline-state.example.json` 的 schema 初始化。
   - 存在：恢复状态，从当前批次继续。
4. 读便签墙 `.harness/state/wall/<feature>.md`，把未关闭的便签带入当前批次。

## 状态与文件

- 状态文件：`.harness/state/pipeline-desktop-<feature>.json`，schema 版本 `1.1`。
- 活跃阶段：`active_stages` 数组记录当前并行运行的阶段 id；无并行时只含一个阶段。
- 阶段交接：`.harness/state/tasks/<feature>-<stage>.md`，必须使用 `.harness/templates/pipeline-handoff.md.template`。
- 阶段日志：`.harness/state/logs/<feature>-<stage>.log`。
- 便签墙：`.harness/state/wall/<feature>.md`，使用 `.harness/templates/sticky-wall.md.template`。
- 最终报告：`.harness/state/reports/pipeline-desktop-<feature>.md`。

状态取值：

- 流水线：`not_started` / `running` / `blocked` / `done`
- 阶段：`queued` / `running` / `passed` / `failed` / `skipped`

## 执行规则：拓扑批次推进

1. 每轮计算 `ready` 阶段：状态为 `queued`，且所有 `depends_on` 阶段均为 `passed`。
2. 对 `ready` 阶段按 `write_scope` 做并行仲裁：
   - 两个阶段无依赖关系，且 `write_scope` 无交集时，可并行启动。
   - `write_scope` 有交集时，禁止并行，按配置顺序降级为串行，并在 journal 记录 `write_conflict`。
3. 把本轮实际启动的阶段 id 写入 `active_stages`，状态置 `running`。
4. 每个阶段独立执行：
   1. 创建任务卡，写入 scope、阶段目标、门禁、handoff 路径和写权边界。
   2. 读取对应角色契约（`.harness/agents/pipeline/<role>.md`）。
   3. 执行阶段 Agent：优先使用 Codex 桌面版多智能体子任务机制；不可用时由协调者按角色契约代理执行，但必须独立写 handoff。
   4. 校验 handoff：文件存在、`conclusion` 合法、必需字段完整；`review` 阶段额外校验 `review_verdict` 为 `pass` / `rework` / `needs_owner`。
   5. 运行门禁命令并记录退出码。
   6. 追加 journal，更新阶段状态。
5. 任一阶段完成后，从 `active_stages` 移除并重新计算下一批 `ready` 阶段。
6. 平台不支持真并行时，保持“并行批次语义 + 串行 fallback”：仍按批次计算，但逐个执行，并把 fallback 记入 journal。

## 写权仲裁

- 阶段在 pipeline 配置中声明 `write_scope`，未声明时默认只写自己的 handoff 产物。
- 并行启动前必须检查两两 `write_scope` 交集。
- 冲突处理：拒绝并行，改为串行；`write_conflict` 写入 journal；不覆盖任何阶段已写文件。
- 运行期登记：协调者在状态文件的阶段记录中保留 `write_scope`，作为审计依据。
- 静态写权矩阵见 `.harness/agents/pipeline/README.md`，运行时仲裁以本协议为准。

## 便签墙

- 便签用于记录跨阶段共享的决策、风险、待确认项和事实。
- 阶段 Agent 只能追加便签，不得修改或删除已有便签；协调者可以关闭便签。
- 每个阶段开始前必须读墙，结束时可追加便签。
- 便签 ID 固定格式 `N<序号>`，类型为 `decision` / `risk` / `question` / `fact`。
- 便签墙不提交 Git，属于运行期产物。

## debate 轻量版

- `review` 阶段输出 `review_verdict` 时，同时输出 `main_opinion`、`opposing_opinion`、`decision_basis`。
- 当出现以下任一情况时，协调者发起一轮辩论：
  - verdict 为 `needs_owner`；
  - 同一 review 出现两个评审子任务且结论冲突；
  - 便签墙存在未关闭的 `question` 且影响验收。
- 辩论流程：
  1. 读取 `.harness/agents/pipeline/debater.md` 角色契约。
  2. 启动两个评审子任务，分别代表“支持通过”和“要求返工”的立场。
  3. 双方各输出一轮意见，写入 `debate_round` journal 和便签墙。
  4. 协调者按证据和验收标准裁决，输出 `pass` / `rework` / `needs_owner`。
- 轻量版只做一轮；多轮辩论与评分留作后续扩展。

## 门禁与重试

1. 门禁失败：
   - `attempts + 1`，未达 `max_attempts` 时重试。
   - 达到上限后标记 `blocked`，升级 Owner。
2. escalation：
   - `blocking=true`：停止流水线，标记 `blocked`，问 Owner。
   - `blocking=false`：记入 journal，按 `default_if_ignored` 继续。
3. 评审打回：
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
