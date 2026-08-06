# Harness 模板

本目录提供 Codex-only 的 Harness 入口模板和初始化脚本，用于为新的后端项目搭建 `.harness` 体系骨架。

## 文件说明

- `AGENTS.md.template`：新项目智能体入口模板，包含文件定位、目录与知识索引、任务路由、修改边界、验证入口和禁止事项。
- `script\harness-init.ps1`：一键初始化脚本，生成目标项目的 `.harness` 骨架和 `AGENTS.md`。

## 使用方式

从本仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File script\harness-init.ps1 -Target C:\path\to\new-project -ProjectName my-project
```

`-Target` 必填，`-ProjectName` 可选；未传时使用目标目录名。目标目录不存在时自动创建；目标目录已存在且已有 `AGENTS.md` 时跳过，不覆盖任何内容。

初始化完成后，项目根目录会包含：

- `.harness\` 骨架目录：`rules`、`skills`、`changes\active`、`changes\completed`、`wiki`、`templates`、`agents`
- `AGENTS.md`：由模板生成，`{{PROJECT_NAME}}` 已替换，`{{PROJECT_DESC}}`、`{{ENABLED_MODULES}}` 保留为 `TODO` 标记，需项目实例化时填写。

## 可复用内容

- `.harness` 目录骨架约定
- `AGENTS.md` 入口结构、任务路由和修改边界
- 验证入口约定（`script\check.ps1`、Maven 模块测试）
- 状态文件位置约定（`PROGRESS.md`、`feature-list.json`）

## 必须项目实例化

- `ARCHITECTURE.md`：真实架构、模块装配和边界
- 项目 owner：`.harness\agents\owner.md`
- 具体规则：`.harness\rules\`（编码、Git、SQL、文档等）
- 具体技能：`.harness\skills\`
- 状态与变更：`.harness\changes\active\feature-list.json`、`changes\completed\INDEX.md`
- 项目知识：`.harness\wiki\`
- 项目验证脚本：`script\check.ps1`

## 边界

当前模板是 Codex-only，不包含 Claude 配置。模板只提供通用骨架，不复制本仓库的业务设计、数据模型、应用核心方案或模块实例化内容。
