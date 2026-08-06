# .harness/rules/tool-access.md

## 1. 文件定位

本规则定义智能体在任务中可使用和禁用的工具边界，遵循最小权限原则。

## 2. 默认允许

- 文件读取、搜索、路径检查和只读分析。
- 当前任务范围内的文件编辑。
- 构建、测试、打包、启动检查命令。
- 只读 SQL 查询和数据库结构核对。
- 读取配置、文档、日志和测试报告。

## 3. 需要暂停确认

- 删除文件或目录、递归移动、覆盖用户已有改动。
- 修改未启用模块、根 `pom.xml`、`app-server/pom.xml` 或 `app-framework`。
- 破坏性 SQL、批量数据修复、删表删字段。
- 生产环境命令、密钥管理、Token 策略变更。
- `git reset --hard`、force push 等破坏性 Git 操作。
- 网络外发敏感信息或访问生产接口。

## 4. 最小权限原则

- 只授予完成任务所需的最小工具范围。
- 不绕过认证、权限、租户和数据权限。
- 工具不可用时，说明原因和影响，不伪造验证结果。

## 5. Codex 侧强制与配置

- Codex 的沙箱、审批和 MCP 服务配置在 `.codex/config.toml`，与用户级配置合并读取；只启用任务所需最小权限，MCP 必须由用户确认后启用。
- 技能同步检查使用 `script/sync-skills.ps1`，运行前确认技能目录与同步结果。
- Git 推送门禁由 `script/install-hooks.ps1` 安装 pre-push hook，hook 调用 `script/sync-changes.ps1 -PushGate`；当前目录非 Git 仓库时按 `.harness/rules/git-workflow.md` 降级，不阻塞。
