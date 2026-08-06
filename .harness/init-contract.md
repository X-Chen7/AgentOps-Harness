# 初始化契约（当前项目）

## 启动命令

- 统一验证：`script/check.ps1`
- 技能同步：`script/sync-skills.ps1`
- Git 协作：`script/harness-git.ps1` 与 `script/install-hooks.ps1`
- 新项目初始化：`script/harness-init.ps1 -Target <path> -ProjectName <name>`

## 完成标志

- [ ] 从零克隆后可按上述命令完成校验、技能同步和状态读取。
- [ ] 示例或最小模块测试通过，或明确记录失败原因和未验证范围。
- [ ] `PROGRESS.md` 和 `changes/active/feature-list.json` 已更新。
- [ ] 无临时文件残留，验证结果已回填。
