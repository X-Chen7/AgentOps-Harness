# Harness changes 团队协作 Git 同步增强

## 1. 任务目标

- 目标：落地 `.harness/changes` 的 Git 团队协作同步能力，包括规则、字段、脚本、模板、索引和记录。
- 非目标：不修改后端业务代码；不自动执行 `git push`。
- 成功标准：`script/check.ps1` 通过；所有建议文件落地并在 changes 中写明修改点。

## 2. 背景和上下文

- 需求来源：用户对 `.harness/changes` 的优化建议，重点为团队协作 git commit/push 同步。
- 当前现象：feature-list 缺少 owner、branch、commit、push_status、pr_url、history；开发流程没有 Git 步骤；校验脚本不检查 Git 状态；completed 缺少统一索引。
- 已确认信息：当前目录不是 Git 仓库，Git 功能必须支持非 Git 目录降级。
- 未确认信息：远端仓库地址、团队分支命名和 PR 平台。

## 3. 影响范围

| 范围 | 说明 |
| --- | --- |
| 后端模块 | 无 |
| 框架模块 | 无 |
| 启动装配 | 无 |
| SQL | 无 |
| 配置 | 无 |
| 接口协议 | 无 |
| 权限和安全 | 无 |
| Harness 文档 | 规则、模板、README、PROGRESS、feature-list、changes 记录 |
| 脚本 | harness-check.ps1、sync-changes.ps1、install-hooks.ps1 |

## 4. 执行步骤

1. 新增 `.harness/rules/git-workflow.md`。
2. 扩展 `feature-list.json` 和模板字段及状态机。
3. 扩展 `script/harness-check.ps1` 的 Git 与 schema 校验。
4. 新增 `script/sync-changes.ps1` 和 `script/install-hooks.ps1`。
5. 新增 commit/PR 模板、completed INDEX 和会话交接 Git 字段。
6. 更新 README、PROGRESS 和 changes 记录。
7. 运行 `script/check.ps1` 和 `script/sync-changes.ps1` 验证。

## 5. 验证计划

| 验证项 | 命令或方式 | 预期结果 |
| --- | --- | --- |
| 统一检查 | `script/check.ps1` | 通过 |
| changes 同步检查 | `script/sync-changes.ps1` | 非 Git 目录时提示 skip 并退出 0 |
| 后端验证 | 不涉及，跳过 | 无 |

## 6. 风险和审批

- 风险点：当前目录不是 Git 仓库，commit/push 无法实际执行，只能提供机制。
- 是否涉及数据库变更：否。
- 是否涉及权限模型：否。
- 是否涉及外部系统：否。
- 是否需要 Owner 审批：完成后需 Owner 确认 Git 远端和分支策略。

## 7. 当前状态

- 状态：in_progress
- 当前进展：规则、模板、字段、脚本、校验和索引均已实现，等待统一检查。
- 阻塞点：无。

## 8. 退出条件

- 所有建议文件已落地。
- `script/check.ps1` 通过。
- 修改点已写入 completed 记录和 INDEX。

## 9. 完成定义（DoD）

- 验证命令：`script/check.ps1` 通过。
- 验收条件：Git 规则可读、feature-list 字段完整、校验脚本可运行、模板和索引存在。
- 文档同步：`.harness/README.md`、AGENTS.md、PROGRESS.md、changes README 已更新。

## 10. 状态与交接

- 当前进度写入 `.harness/PROGRESS.md`。
- 功能状态写入 `feature-list.json`。
- 完成后计划归档至 `changes/completed/archive/`。

## 11. 生命周期规则

- 状态变为 completed 后移入 `changes/completed/archive/`。
- 同一主题只保留一个计划文件。
