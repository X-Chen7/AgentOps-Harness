# PowerShell 工具链迁移到 Python CLI（F-011）完成记录

## 1. 完成摘要

- 完成日期：2026-08-07
- 执行人：AgentOps-Harness 维护
- 关联计划：`changes/completed/archive/2026-08-07-python-cli-migration.md`
- 关联 PR：https://github.com/X-Chen7/AgentOps-Harness/pull/3
- 当前结论：PowerShell 工具链迁移为 Python CLI，旧入口保持兼容，测试与 CI 落地。

## 2. 实际改动

| 文件 | 改动 |
| --- | --- |
| `harness/` | 新增 Python CLI 包：check、sync、sync-skills、init、install-hooks、commit、push、pr |
| `pyproject.toml` | 新增包配置与 `harness` 入口 |
| `script/*.ps1` | 全部改为调用 Python CLI 的薄包装，旧命令兼容 |
| `tests/` | 新增 14 个 pytest 测试 |
| `.github/workflows/ci.yml` | 新增 GitHub Actions CI |
| README / AGENTS / Harness 文档 | 更新为 Python CLI 主入口 |

## 3. 功能能力

- `harness check`：Harness 结构、schema、write_scope、active_stages 等校验。
- `harness sync`：feature-list 与 Git 状态门禁。
- `harness sync-skills`：技能同步与一致性检查。
- `harness init` / `install-hooks`：新项目初始化和 pre-push hook。
- `harness commit/push/pr`：feature 分支、提交、推送和 PR 自动化。

## 4. 验证结果

| 验证项 | 结果 |
| --- | --- |
| `python -m pytest -q` | 14 passed |
| `python -m harness check` | 0 error |
| `script/check.ps1` | 0 error，旧入口兼容 |
| 跨目录调用 | Python CLI 与包装脚本均可从任意目录运行 |
| push 门禁负向验证 | 未提交文件时正确退出码 1 |

## 5. 审计发现与不足

| 不足 | 处理 |
| --- | --- |
| `harness pr` 依赖 gh 且需要额外 scope | 本次通过 GitHub REST API 创建 PR；后续可给 CLI 增加 REST fallback |
| PowerShell 包装依赖本机 Python | README 已提供 `pip install -e .` 安装方式 |

## 6. 遗留风险与下一步

| 风险/事项 | 建议处理 |
| --- | --- |
| GitHub 语言统计有缓存 | 合并后等待 GitHub 重新统计，必要时强制刷新 |
| 真实 PR 自动化仍依赖 gh | 后续为 `harness pr` 增加 GitHub REST API fallback |
