# Harness 状态与反馈子服务优化完成记录

## 1. 完成摘要

- 完成日期：2026-08-05
- 执行人：Codex
- 关联计划：`.harness/README.md`、`AGENTS.md`、`script/check.ps1`
- 当前结论：按 Learn Harness Engineering 五子服务模型补齐状态层、反馈层、工具边界和完成定义，入口文件完成精简。

## 2. 原始目标

- 增加跨会话状态：PROGRESS 和机器可读功能清单。
- 增加统一验证入口和独立完成判定。
- 补齐初始化契约、会话交接和工具权限边界。
- 精简 `AGENTS.md`，把详细索引下沉到 `.harness/README.md`。

## 3. 实际改动

| 类型 | 改动说明 |
| --- | --- |
| 状态层 | 新增 `.harness/PROGRESS.md` 和 `.harness/changes/active/feature-list.json`，固化 WIP=1 |
| 反馈层 | 新增 `script/check.ps1`，默认跑 Harness 检查，`-Backend` 时跑 Maven 模块测试和服务打包 |
| 完成定义 | `changes/active/README.md` 增加 DoD、验证门禁、状态交接规则 |
| 模板 | 新增 `templates/`：PROGRESS、feature-list、init-contract、session-handoff 模板 |
| 工具边界 | 新增 `.harness/rules/tool-access.md` |
| 环境契约 | 新增 `.harness/init-contract.md` |
| 入口精简 | `AGENTS.md` 从 167 行精简到 120 行，完整知识坐标移入 `.harness/README.md` |
| 规则同步 | `development-flow.md` 增加统一验证入口、PROGRESS/feature-list 更新要求和独立评审门禁 |
| 迁移指南 | `app-harness-migration-guide.md` 增加 `templates/` 和 `tool-access.md` 可复制项 |

## 4. 验证结果

| 验证项 | 命令或方式 | 结果 |
| --- | --- | --- |
| Harness 健康检查 | `script/harness-check.ps1` | 0 error，2 warning |
| 统一检查入口 | `script/check.ps1` | 通过；后端 Maven 默认跳过 |
| 入口行数 | `AGENTS.md` | 120 行 |

## 5. 决策记录

- WIP=1 只约束 `in_progress`，`ready_for_review` 可排队等待确认。
- 功能状态以 JSON 为机器可读权威，Markdown 计划只做解释和上下文。
- `script/check.ps1` 默认不跑完整 Maven，避免把已知的既有测试环境问题变成每次检查的硬失败；需要完整后端验证时显式使用 `-Backend`。

## 6. 遗留风险

| 风险 | 影响 | 建议处理 |
| --- | --- | --- |
| 两份 wiki 文档超过 40KB | 维护成本较高 | 按专题拆分或改为生成式接口清单 |
| `feature-list.json` 与 Markdown 计划需同步维护 | 可能漂移 | 每次状态变化同时更新两处，由校验脚本检查 WIP 和计划链接 |
| 根目录不是 git 仓库 | 无法落地干净提交检查点 | 接入版本管理后补充提交和 worktree 规范 |

## 7. 后续行动

- 每次会话结束更新 `PROGRESS.md` 和 `feature-list.json`，运行 `script/check.ps1`。
- L3/L4、权限安全、SQL、跨模块改动进入 `ready_for_review` 前执行 `expert-reviewer`。
- 后续可把 `script/check.ps1 -Backend` 接入 CI 或定时检查。
