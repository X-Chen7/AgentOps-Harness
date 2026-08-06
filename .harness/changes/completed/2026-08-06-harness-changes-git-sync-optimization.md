# Harness changes 团队协作 Git 同步增强 完成记录

## 1. 完成摘要

- 完成日期：2026-08-06
- 执行人：Harness 维护
- 关联 active 计划：`changes/completed/archive/2026-08-06-harness-changes-git-sync-optimization.md`
- 关联 commit：未记录（当前目录非 Git 仓库）
- 关联 PR：未记录
- 当前结论：前面提出的 P0/P1/P2 建议已全部落地，`script/check.ps1` 通过。

## 2. 原始目标

- 目标：补齐 `.harness/changes` 的团队协作 Git 同步能力，并增加 owner、分支、commit、push、PR、跨仓库等状态字段。
- 非目标：不修改后端业务代码；不自动执行 `git push`。
- 成功标准：规则、字段、校验脚本、同步脚本、hooks、模板、索引全部落地，并在 changes 中写明修改点。

## 3. 实际改动（修改点）

| 文件 | 修改点 | 类型 |
| --- | --- | --- |
| `.harness/rules/git-workflow.md` | 新增 Git 协作规则：分支规范、commit 规范、push/PR 门禁、状态同步、非 Git 目录降级 | 新增 |
| `.harness/changes/active/feature-list.json` | schema 升级到 1.1，新增 `git_sync`；feature 增加 `owner`、`repo`、`branch`、`commit`、`push_status`、`pr_url`、`remote_branch`、`sync_repos`、`depends_on`、`issue_id`、`updated_at`、`history`；新增 F-003 | 修改 |
| `.harness/templates/feature-list.json.template` | 模板同步升级字段和状态机 | 修改 |
| `.harness/templates/session-handoff.md.template` | 增加 Git 同步章节：分支、commit、push 状态、PR 链接、feature-list 回写 | 修改 |
| `.harness/templates/commit-message.md.template` | 新增 commit message 模板，要求引用 feature ID 并写清验证方式 | 新增 |
| `.harness/templates/pr-description.md.template` | 新增 PR/MR 描述模板，包含关联、验证、同步项和遗留风险 | 新增 |
| `script/harness-check.ps1` | 状态机扩展；新增 push_status、owner、history 校验；新增 Git 仓库检测、`git diff --check`、commit/branch 校验；PROGRESS 与 feature-list 一致性检查；completed INDEX 链接校验；新增模板和脚本存在性检查 | 修改 |
| `script/sync-changes.ps1` | 新增 changes 同步检查：feature-list/PROGRESS 一致性、active 计划状态、Git 工作区、commit 与分支映射；支持 `-PushGate` | 新增 |
| `script/install-hooks.ps1` | 新增 pre-push hook 安装脚本，非 Git 仓库时自动跳过 | 新增 |
| `.harness/changes/completed/INDEX.md` | 新增完成记录和归档计划索引，登记日期、commit、PR、仓库 | 新增 |
| `.harness/changes/active/README.md` | 状态值扩展为完整状态机，补充 Git 字段回写规则和 sync-changes 门禁 | 修改 |
| `.harness/changes/completed/README.md` | 完成记录增加 commit/PR 字段，补充 INDEX 维护规则 | 修改 |
| `.harness/README.md` | 知识坐标增加 Git 规则、完成索引、同步脚本、hooks 安装；维护规则补充 Git 绑定和 INDEX 要求 | 修改 |
| `.harness/rules/development-flow.md` | 新增第 20 节 Git 提交与推送同步流程 | 修改 |
| `AGENTS.md` | 常用入口增加 Git 协作规则和 sync-changes 脚本 | 修改 |
| `.harness/PROGRESS.md` | 更新日期、当前任务、进行中项、验证结果 | 修改 |

## 4. 验证结果

| 验证项 | 命令或方式 | 结果 |
| --- | --- | --- |
| 统一检查 | `script/check.ps1` | 通过 |
| changes 同步检查 | `script/sync-changes.ps1` | 非 Git 目录提示 skip 并退出 0 |
| JSON 解析 | `ConvertFrom-Json` 校验 `feature-list.json` | 通过 |
| 索引链接 | `harness-check` 校验 `INDEX.md` 链接 | 通过 |

无法验证项：

- 验证项：真实 `git push` / pre-push hook 行为。
- 原因：当前目录不是 Git 仓库。
- 风险：恢复 Git 仓库后需要先安装 hooks 并回填远端信息。

## 5. 决策记录

- 决策：Git 同步机制完整落地，但 `git_sync.enabled` 保持 `false`。
- 原因：当前目录不是 Git 仓库，避免校验脚本误报。
- 替代方案：强制要求先初始化 Git 仓库再落地。
- 放弃原因：会阻塞当前工作副本的 Harness 治理，且用户未提供远端仓库地址。

## 6. 遗留风险

| 风险 | 影响 | 建议处理 |
| --- | --- | --- |
| 未配置远端和分支策略 | commit/push 同步无法实测 | 恢复 Git 仓库后执行 `script/install-hooks.ps1`，回填 `git_sync` 并确认分支规则 |
| F-001 / F-002 owner 为“待补充” | 团队责任人不明确 | Owner 确认后回填 owner、branch、commit、history |
| 历史完成记录缺少 commit/PR | 无法从 Git 反查历史 | 结合远端日志逐步回填 INDEX |

## 7. 后续行动

- 是否需要新增 tech-debt-tracker 条目：暂不新增；仓库恢复后若 hooks 无法运行再登记。
- 是否需要补充 wiki：无需；规则已写入 `.harness/rules/git-workflow.md`。
- 是否需要通知前端、测试或运维：需团队 Owner 确认 Git 远端和分支策略。
- 是否需要继续拆分新 active 计划：无需，本次任务已闭环。
