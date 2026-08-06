# Codex 桌面版多智能体迁移完成记录

## 1. 完成摘要

- 完成日期：2026-08-06
- 执行人：Harness 维护
- 关联计划：`changes/completed/archive/2026-08-06-harness-cli-executable-pipeline.md`
- 关联 commit：本次迁移提交（`git log -1` 可查）
- 关联 PR：未记录
- 当前结论：harness-cli v1 正式退役并归档，Git/PR 自动化拆为独立 `script/harness-git.ps1`；编排由 Codex 桌面版多智能体角色接管。

## 2. 实际改动

| 文件 | 改动 |
| --- | --- |
| `.harness/archive/harness-cli/` | 归档 `harness.cmd`、`script/harness-cli.ps1`、`script/lib/codex-executor.ps1`、`pipelines/default.json` |
| `script/harness-git.ps1` | 新增独立 Git/PR 命令：commit/push/pr，替代 harness-cli 内嵌 Git 逻辑 |
| `.harness/agents/pipeline/` | 新增协调者 + 分析/编码/测试/评审 5 个角色契约 |
| `.harness/pipelines/desktop-coordinator.md` | 新增桌面版流水线流程提示词 |
| `script/harness-check.ps1` | 移除 live 对 harness-cli、codex-executor、default.json 的必检，保留 state 与 pipeline 字段校验 |
| `.harness/README.md` | 知识坐标改为桌面版角色/流程、harness-git、已退役归档 |
| `.harness/PROGRESS.md` | 登记第八轮迁移，F-007 标注退役 |
| `.harness/state/README.md` | 状态目录改由桌面版流水线使用 |
| `.harness/changes/active/feature-list.json` | F-001 流水线状态重置为 not_started，清理 harness-cli 运行历史；F-007 补充退役说明；开启 git_sync |
| `.harness/changes/completed/INDEX.md` | 追加本完成记录 |

## 3. 验证结果

| 验证项 | 命令或方式 | 结果 |
| --- | --- | --- |
| PowerShell 语法 | Parser | `harness-git.ps1`、`harness-check.ps1` 0 error |
| 统一检查 | `script/check.ps1` | 0 error |
| 变更同步 | `script/sync-changes.ps1` | 0 error（仓库有未提交路径时仅 warning） |
| Git/PR 拦截 | 未知 feature / push 无 remote / pr 未推送 | 按预期拦截 |
| JSON 解析 | feature-list ConvertFrom-Json | 7 个 feature 可解析，F-001 为 not_started |

## 4. 决策记录

- 不再维护 harness-cli 运行器，保留源码归档供复用和复盘。
- 可执行流水线改为 Codex 桌面版多智能体：协调者负责流程和门禁，阶段角色按需加载。
- Git/PR 自动化独立成 `harness-git.ps1`，可由任何 Agent 或人工调用，不绑定 CLI 编排。

## 5. 遗留风险

| 风险 | 影响 | 建议处理 |
| --- | --- | --- |
| 桌面版流水线尚未用真实 feature 完整跑一遍 | analysis/coding/test/review 联动和门禁仍有验证缺口 | 用 F-001 或新 feature 走一次桌面版编排 |
| 当前仓库无 remote | push/pr 无法执行 | 配置 origin 后再验证 push/PR |
| `.harness/state/` 运行产物被 .gitignore 忽略 | 跨设备/跨会话状态不会进 Git | 需要共享时改用 feature-list 或 CI 持久化 |
