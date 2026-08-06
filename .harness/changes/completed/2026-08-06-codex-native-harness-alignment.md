# Codex 原生 Harness 对齐 完成记录

## 1. 完成摘要

- 完成日期：2026-08-06
- 执行人：Harness 维护 + 4 个多智能体并行
- 关联 active 计划：`changes/completed/archive/2026-08-06-codex-native-harness-alignment.md`
- 关联 commit：未记录（当前目录非 Git 仓库）
- 关联 PR：未记录
- 当前结论：P0-P3 全部落地，`script/check.ps1` 通过。

## 2. 原始目标

- 目标：Codex-only 补齐技能自动发现、配置与门禁、模块化入口、模板与基准。
- 非目标：不使用 Claude，不激活可能破坏本机 Codex 配置的设置。
- 成功标准：检查通过，改动点写入 changes。

## 3. 实际改动（修改点）

| 文件 | 修改点 | 类型 |
| --- | --- | --- |
| `.codex/skills/` | 9 个技能从 `.harness/skills/` 完整同步（含 SKILL.md 和 agents/openai.yaml） | 新增 |
| `script/sync-skills.ps1` | 技能同步/哈希校验脚本，支持 `-Check` | 新增 |
| `.codex/config.toml` | 项目级 Codex 配置骨架，仅注释和注释示例，不激活模型/沙箱/审批/MCP | 新增 |
| `.codex/README.md` | Codex 项目配置说明、安全配置建议、MCP 接入说明（数据库只读、浏览器待用户确认） | 新增 |
| `.harness/rules/tool-access.md` | 新增第 5 节“Codex 侧强制与配置” | 修改 |
| `AGENTS.md` | 根入口精简为文件定位 + 三个 `@` 导入 | 修改 |
| `AGENTS.d/00-common.md` | 目录与知识索引、项目实例化索引、任务路由、Harness 知识坐标 | 新增 |
| `AGENTS.d/01-boundaries.md` | 修改边界、禁止事项 | 新增 |
| `AGENTS.d/02-verification.md` | 验证入口、Agent 工作流程 | 新增 |
| `app-module-user/AGENTS.md` | 模块职责、边界、wiki、验证命令 | 新增 |
| `app-module-infra/AGENTS.md` | 模块职责、边界、wiki、验证命令 | 新增 |
| `app-module-app-core/AGENTS.md` | 模块职责、边界、wiki、验证命令 | 新增 |
| `script/harness-check.ps1` | 校验 AGENTS `@` 导入、Codex 技能同步、`.codex` 配置、模块级 AGENTS、模板和基准产物 | 修改 |
| `harness-template/AGENTS.md.template` | Codex 风格入口模板，含占位符 | 新增 |
| `harness-template/README.md` | 模板使用说明、可复用/需实例化内容 | 新增 |
| `script/harness-init.ps1` | 新项目 Harness 初始化脚本，纯 ASCII | 新增 |
| `benchmark/README.md` | 7 个基准任务 B-01 到 B-07，5 项对比指标 | 新增 |
| `.harness/README.md` | 知识坐标补充 Codex 配置、技能同步、模板和基准入口 | 修改 |
| `.harness/changes/active/feature-list.json` | 新增 F-004 并标记 done | 修改 |
| `.harness/PROGRESS.md` | 更新日期、已完成项、验证结果 | 修改 |
| `.harness/changes/completed/INDEX.md` | 新增完成记录和归档计划索引 | 修改 |

## 4. 验证结果

| 验证项 | 命令或方式 | 结果 |
| --- | --- | --- |
| 统一检查 | `script/check.ps1` | 通过（0 error，2 个既有大文档 warning） |
| 技能同步 | `script/sync-skills.ps1 -Check` | `OK: files match` |
| 配置合法性 | TOML 解析 `.codex/config.toml` | 合法，无激活项 |
| 模板初始化 | 临时目录实测 `harness-init.ps1` | 创建成功，二次执行 SKIP |

无法验证项：

- 验证项：Codex 实际自动发现 `.codex/skills`、真实 push 门禁、MCP 连接。
- 原因：当前 Codex 会话技能发现路径以运行环境为准；目录非 Git 仓库；MCP 服务未确认。
- 风险：启用 MCP 和沙箱前必须先验证本机 Codex 配置兼容性。

## 5. 决策记录

- 决策：项目级 `.codex/config.toml` 只放注释和注释示例，不激活设置。
- 原因：本机使用自定义 model provider，激活不确定键可能导致 Codex 启动失败。
- 替代方案：直接写入 sandbox/approval/MCP 配置。
- 放弃原因：缺少用户确认且存在破坏本机配置的风险。

## 6. 遗留风险

| 风险 | 影响 | 建议处理 |
| --- | --- | --- |
| `.codex/skills` 是否被当前 Codex 版本自动发现未实测 | 技能可能仍需用户级安装 | 用真实 Codex 会话验证，必要时把技能装到 `%USERPROFILE%\.codex\skills` |
| MCP 未启用 | 无法接数据库/浏览器 | 用户确认服务后按 `.codex/README.md` 启用 |
| 沙箱/审批未激活 | 规则仍以文档约束为主 | 用户确认后按 CLI 支持的方式启用 |
| 当前目录非 Git 仓库 | Git push 门禁无法实测 | 恢复仓库后执行 `install-hooks.ps1` |

## 7. 后续行动

- 是否需要新增 tech-debt-tracker 条目：暂不新增，验证后按需登记。
- 是否需要补充 wiki：已更新 `.harness/README.md`。
- 是否需要通知前端、测试或运维：需用户确认 MCP 服务和沙箱策略。
- 是否需要继续拆分新 active 计划：无需，本次任务已闭环。
