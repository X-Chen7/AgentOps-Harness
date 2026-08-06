# 项目级 Codex 配置说明

## 作用

- `.codex/config.toml` 是 Codex 的项目级配置，会与用户级配置 `C:\Users\Administrator\.codex\config.toml` 合并读取。
- 本仓库当前只保留注释和示例，不激活模型、沙箱、审批或 MCP 设置，避免覆盖本机用户级 model provider 配置，也不写入可能导致 Codex 启动失败的无效配置。
- 项目级配置不应包含密钥、Token 或本机凭据；团队共享的安全策略和 MCP 示例可放在本文件。

## 推荐安全配置（注释形式）

```toml
# sandbox_mode = "read-only"
# approval_policy = "on-request"
```

启用前验证方法：

- 用 `codex --help`、`codex doctor` 和 `codex exec --strict-config --help` 确认当前 Codex 版本实际支持的键名。
- 先只启用单个键并运行一次命令，确认配置被正确读取且不影响本机 model provider。
- 严格遵循最小权限，任务结束后关闭不需要的沙箱放宽或审批策略。

## MCP 接入方式

Codex 的 MCP 服务配置在 `config.toml` 的 `[mcp_servers.*]` 中，不使用 `.mcp.json`。注释示例已写在 `.codex/config.toml`，包含 `database` 和 `browser` 两个候选：

- 数据库：只允许配置为只读访问，不得启用写入能力。
- 浏览器：仅用于用户明确确认的网页访问或本地调试场景。

两个候选都必须由用户确认后再启用；启用前补齐 `command`、`args`、`env` 的真实占位，并用 `codex mcp list` 确认服务已注册。
