# 验证入口

统一检查入口：

```bash
script/check.ps1              # Harness 与快速检查
script/check.ps1 -Backend     # 包含后端模块测试和服务打包（需 Maven 工程）
```

# Agent 工作流程

每次任务默认按以下顺序执行：

1. 读取 `AGENTS.md`。
2. 根据任务类型跳转 `.harness/` 对应文件。
3. 确认影响范围。
4. 小范围修改。
5. 执行最小验证（优先使用 `script/check.ps1`）。
6. 更新 `.harness/PROGRESS.md` 和 `.harness/changes/active/feature-list.json`。
7. 输出修改点、原因、影响范围、验证结果和遗留风险。
