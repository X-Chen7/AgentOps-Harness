# Codex 原生 Harness 对齐（P0-P3）

## 1. 任务目标

- 目标：只使用 Codex 侧能力补齐 Harness：技能自动发现、项目级配置与门禁、模块化入口、可复用模板和基准测试骨架。
- 非目标：不引入 Claude，不创建 `CLAUDE.md`、`.claude/`；不激活可能破坏本机 Codex 配置的模型/沙箱设置。
- 成功标准：`script/check.ps1` 通过；所有改动点写入 completed 记录。

## 2. 背景和上下文

- 需求来源：用户要求按 P0-P3 计划执行，并指定只用 Codex、多用多智能体。
- 当前现象：技能放在 `.harness/skills/` 不被 Codex 自动发现；无项目级 `.codex` 配置；`AGENTS.md` 单文件；无可复用模板和基准。
- 已确认信息：本机 Codex 用户级配置存在且使用自定义 model provider；项目级 `config.toml` 必须保持合法安全。
- 未确认信息：MCP 具体服务，需用户确认后再启用。

## 3. 影响范围

| 范围 | 说明 |
| --- | --- |
| 新增 | `.codex/`、`AGENTS.d/`、三个模块级 `AGENTS.md`、`harness-template/`、`benchmark/`、`script/sync-skills.ps1`、`script/harness-init.ps1` |
| 修改 | `AGENTS.md`、`script/harness-check.ps1`、`.harness/rules/tool-access.md`、`.harness/README.md`、`feature-list.json`、`PROGRESS.md`、changes 记录 |
| 后端代码 | 无 |

## 4. 执行步骤

1. P0：9 个技能同步到 `.codex/skills/`，新增 `script/sync-skills.ps1`。
2. P1：新增 `.codex/config.toml`（仅注释和注释示例）和 `.codex/README.md`，更新 `tool-access.md` 增加 Codex 侧强制说明。
3. P2：根 `AGENTS.md` 拆分为 `AGENTS.d/` 三份导入文件；为 system、infra、app-core 新增模块级 `AGENTS.md`。
4. P3：新增 `harness-template/`、`script/harness-init.ps1` 和 `benchmark/README.md`。
5. 扩展 `harness-check.ps1`：校验 `@` 导入、Codex 技能同步、Codex 配置、模块级 AGENTS、模板和基准产物。
6. 更新 feature-list、PROGRESS 和 changes 记录。

## 5. 验证计划

| 验证项 | 命令或方式 | 预期结果 |
| --- | --- | --- |
| 统一检查 | `script/check.ps1` | 通过 |
| 技能同步 | `script/sync-skills.ps1 -Check` | `OK: files match` |
| 配置合法性 | TOML 解析 `.codex/config.toml` | 合法，无激活项 |
| 模板初始化 | `script/harness-init.ps1` 临时目录实测 | 创建成功，二次执行 SKIP |

## 6. 风险和审批

- 风险点：沙箱/审批/MCP 均未激活，需用户确认后再启用；当前目录不是 Git 仓库，Git 门禁无法实测。
- 是否需要 Owner 审批：MCP 服务和沙箱策略启用前需要确认。

## 7. 当前状态

- 状态：completed（计划归档至 `changes/completed/archive/`）
- 当前进展：全部步骤完成并验证。
- 阻塞点：无。

## 8. 退出条件

- Codex 侧产物全部落地；
- `script/check.ps1` 通过；
- 改动点已写入 completed 记录和 INDEX。

## 9. 完成定义（DoD）

- 验证命令：`script/check.ps1`、`script/sync-skills.ps1 -Check`。
- 验收条件：技能可同步、入口可导入、配置合法、模板可初始化、基准骨架存在。
- 文档同步：`tool-access.md`、`.harness/README.md`、PROGRESS、feature-list、changes 已更新。
