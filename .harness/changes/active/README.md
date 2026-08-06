# <任务名称>

## 1. 任务目标

- 目标：
- 非目标：
- 成功标准：

## 2. 背景和上下文

- 需求来源：
- 当前现象：
- 已确认信息：
- 未确认信息：

## 3. 影响范围

| 范围 | 说明 |
| --- | --- |
| 后端模块 | 例如 app-module-user |
| 框架模块 | 如无影响写“无” |
| 启动装配 | 如无影响写“无” |
| SQL | 如无影响写“无” |
| 配置 | 如无影响写“无” |
| 接口协议 | 如无影响写“无” |
| 权限和安全 | 如无影响写“无” |

## 4. 执行步骤

1. 阅读相关控制器、Service、Mapper、DO、VO 和 SQL。
2. 确认现有实现边界和复用点。
3. 设计最小改动方案。
4. 修改代码或文档。
5. 同步必要 SQL、配置或接口说明。
6. 执行最小验证。
7. 输出交付说明。

## 5. 验证计划

| 验证项 | 命令或方式 | 预期结果 |
| --- | --- | --- |
| 统一检查 | `script/check.ps1`（含后端用 `-Backend`） | 通过 |
| 模块测试 | mvn -pl <module> -am test | 通过 |
| 服务打包 | mvn -pl app-server -am package -DskipTests | 通过 |
| 接口验证 | curl / Postman / 前端联调 | 符合预期 |
| SQL 检查 | 人工审查或本地执行 | 无破坏性变更 |

## 6. 风险和审批

- 风险点：
- 是否涉及数据库变更：
- 是否涉及权限模型：
- 是否涉及外部系统：
- 是否需要 Owner 审批：

## 7. 当前状态

- 状态：draft / in_progress / blocked / ready_for_review / completed
- 当前进展：
- 阻塞点：

## 8. 退出条件

- 代码或文档改动完成。
- 必要验证完成，或明确说明无法验证原因。
- 风险和遗留问题已记录。
- 如任务完成，已迁移或补充 completed 记录。
- 如属于 L3 / L4、多阶段、权限安全、跨服务或前后端协作需求，已新增或维护需求完成跟踪文档。

## 9. 完成定义（DoD）

- 完成标准必须是可验证条件，不能只写“已完成”。
- 每个 active 计划至少填写：
  - 验证命令：`script/check.ps1` 或 `script/check.ps1 -Backend`
  - 验收条件：接口行为、页面操作、数据结果
  - 文档同步：对应 wiki、前端对接说明、数据模型
- 状态进入 `ready_for_review` 前，必须执行 `expert-reviewer` 和验证门禁。
- 只有独立验证通过后才能置 `completed` 并移入 `completed/archive/`。

## 10. 状态与交接

- 当前进度写入 `.harness/PROGRESS.md`。
- 功能状态写入 `feature-list.json`，状态值固定为 `todo / in_progress / ready_for_review / committed / pushed / merged / blocked / done`。
- 每个 feature 至少维护 `owner`、`branch`、`commit`、`push_status`、`pr_url`、`updated_at`、`history`。
- 状态进入 `committed` 前回写 commit；进入 `pushed` / `merged` 前回写 branch、push_status 和 pr_url。
- 每次状态变化追加 `history`：`{ "status", "at", "by", "note" }`。
- WIP=1：同一时间只允许一个 `in_progress` 功能。
- 会话结束按 `.harness/templates/session-handoff.md.template` 检查交接。

## 11. 生命周期规则

- `active/` 只放 `draft / in_progress / blocked / ready_for_review` 状态计划。
- 状态变为 `completed` 后，计划文件立即移入 `changes/completed/archive/`。
- 同一主题只保留一个计划文件，不新增中英文双份。
- 新计划使用中文业务主题命名，避免与已完成记录混用。
- Git 提交和推送规则见 `.harness/rules/git-workflow.md`；推送前执行 `script/sync-changes.ps1 -PushGate`。
