# .harness/rules/git-workflow.md

## 1. 文件定位

本文件定义团队协作中的 Git 分支、提交、推送、PR 和 `.harness/changes/` 状态同步规则，适用于后端代码、SQL、配置和 Harness 文档变更。

## 2. 分支规范

- 主分支：`main`（或团队约定的集成分支），禁止直接推送。
- 功能分支：`feature/F-<编号>-<短名称>`，例如 `feature/F-001-rbac-oauth2-enhancement`。
- 修复分支：`fix/TD-<编号>-<短名称>` 或 `fix/<issue>-<短名称>`。
- 治理分支：`docs/<短名称>` 或 `chore/harness-<短名称>`。
- 一个功能对应一个分支，分支生命周期与 `feature-list.json` 中对应 feature 保持一致。

## 3. 提交规范

- Commit message 首行建议格式：`<type>(<scope>): <摘要> Ref: <F-ID/TD-ID>`，简单改动可用 `F-001: <摘要>`。
- 建议类型：`feat` / `fix` / `docs` / `refactor` / `test` / `chore`。
- Commit body 至少说明：改了什么、为什么改、如何验证；涉及 SQL 或接口变更时显式标注。
- 每个功能至少有一个 commit 引用对应 feature ID，便于从 Git 反查变更计划。
- 禁止把多个不相关功能混入同一个 commit。

## 4. 推送与 PR

- push 前必须执行 `script/check.ps1`；涉及后端代码时执行 `script/check.ps1 -Backend`。
- push 前必须同步更新 `PROGRESS.md` 和 `feature-list.json` 中的状态、branch、commit、push_status。
- 团队仓库建议执行 `script/install-hooks.ps1` 安装 pre-push 门禁，之后 push 自动运行 `script/sync-changes.ps1 -PushGate`。
- 功能分支合入集成分支前必须经过 PR/MR 评审；L3/L4、权限安全、OAuth2、SQL 或跨模块改动必须经过 `expert-reviewer`。
- 禁止 `force push` 到共享分支，禁止 `git reset --hard` 覆盖他人改动。

## 5. 状态同步规则

feature-list 状态机：

`todo -> in_progress -> ready_for_review -> committed -> pushed -> merged -> done`

- `committed`：代码已提交，commit 字段必填。
- `pushed`：分支已推送，commit、branch 必填，push_status 为 `pushed`，有 PR 时填写 pr_url。
- `merged`：PR 已合入，push_status 为 `merged`。
- `done`：独立验证完成且 completed 记录已补充。
- `blocked`：存在阻塞，必须填写 blocked_by。

每次状态变化写入 `history`：`{ "status": "...", "at": "YYYY-MM-DD", "by": "...", "note": "..." }`。

## 6. Issue/PR 自动同步

- 每个 feature 对应一个 GitHub Issue，`Feature ID: F-XXX` 写入 Issue 正文、PR 标题或正文、分支名。
- `feature-list.json` 是机器权威；GitHub Issue/PR 是外部投影，事件触发后由 `harness github sync` 重新计算并回写。
- Issue opened 自动创建 feature 和计划；PR opened 回写 `pushed`、`pr_url`、`pr_number`；PR merged 自动归档、更新 INDEX/PROGRESS、重建 knowledge index 并关闭关联 Issue。
- PR closed 未合并回退 `in_progress`；Issue closed 未合并置 `blocked`。
- `harness github sync --strict` 用于 CI 门禁；重复事件幂等，机器字段以台账为准，标题冲突不静默覆盖。

## 7. 非 Git 目录降级

当前目录可能不是 Git 仓库（例如复制出的工作副本）：

- `script/check.ps1` 跳过 Git 校验并提示；
- `script/sync-changes.ps1` 输出 skip，不阻塞；
- `feature-list.json` 的 `git_sync.enabled` 保持 `false`；
- 恢复为 Git 仓库后，先安装 hooks，再开启 `git_sync.enabled = true`。

## 8. 禁止事项

- 不自动执行 `git push`；是否推送由用户或团队明确要求。
- 不执行破坏性 Git 操作。
- 不提交或推送未验证改动。
- 不把 commit/PR 信息只写在聊天记录里，必须回写 feature-list 和完成记录。
