# harness-cli 可执行流水线 v1 完成记录

## 1. 完成摘要

- 完成日期：2026-08-06
- 执行人：Harness 维护 + 2 个多智能体并行
- 关联计划：`changes/completed/archive/2026-08-06-harness-cli-executable-pipeline.md`
- 关联 commit：未记录（当前目录非 Git 仓库）
- 关联 PR：未记录
- 当前结论：`harness-cli` v1 已落地，dry-run、状态命令和 `script/check.ps1` 通过；真实 `analysis` 阶段已在本机跑通并通过门禁。

## 2. 实际改动

| 文件 | 改动 |
| --- | --- |
| `script/harness-cli.ps1` | 新增主命令：run/status/report/reset/stage；阶段编排、门禁执行、状态回写、报告生成 |
| `harness.cmd` | 新增启动器，不带参数运行进入交互式菜单 |
| `script/lib/codex-executor.ps1` | 新增 Codex CLI 适配器，调用 `codex exec` 并回传退出码 |
| `.harness/pipelines/default.json` | 新增默认流水线：analysis/coding/test/review |
| `.harness/templates/pipeline-task-card.md.template` | 新增阶段任务卡模板 |
| `.harness/templates/pipeline-report.md.template` | 新增报告模板 |
| `.harness/state/` | 新增状态目录：pipeline JSON、tasks、logs、reports |
| `.harness/changes/active/feature-list.json` | schema 升级 1.2，所有 feature 增加 `pipeline` 字段，新增 F-007 |
| `script/harness-check.ps1` | 校验流水线配置、执行器、模板、state、pipeline 字段 |
| `.harness/README.md`、`PROGRESS.md`、`INDEX.md` | 登记 F-007 |

## 3. 验证结果

| 验证项 | 命令或方式 | 结果 |
| --- | --- | --- |
| 语法检查 | PowerShell Parser | `harness-cli.ps1`、`codex-executor.ps1` 0 error |
| dry-run | `harness-cli run -Feature F-001 -DryRun` | 打印 4 个阶段和门禁，exit 0 |
| 交互菜单 | `harness.cmd`（管道模拟选择） | 菜单显示、选择 feature、dry-run、退出均正常 |
| 状态命令 | `harness-cli status -Feature F-001` | 返回 not_started |
| JSON 解析 | `feature-list.json` ConvertFrom-Json | schema 1.2，7 个 feature 可解析 |
| 统一检查 | `script/check.ps1` | 0 error，2 个既有大文档 warning |
| 真实阶段运行 | `harness-cli stage -Feature F-001 -Stage analysis -TimeoutSeconds 300` | analysis 通过，门禁 `script/check.ps1` exit 0 |

## 4. 决策记录

- 采用 2A：Codex CLI 作为 Agent 执行器，失败时明确报错，不自动降级。
- Git/PR 阶段保持 `enabled: false`，不自动 push。
- 流水线状态以 `.harness/state/pipeline-<feature>.json` 为运行期事实，feature-list 的 `pipeline` 字段为对外状态。

## 5. 遗留风险

| 风险 | 影响 | 建议处理 |
| --- | --- | --- |
| 仅实测 analysis 阶段 | coding/test/review 仍可能有授权、沙箱或参数问题 | 完整运行 `harness-cli run -Feature <id>` 继续验证 |
| 当前目录非 Git 仓库 | Git/PR 阶段无法使用 | 恢复仓库后开启 `git_pr.enabled` |
| `test` 阶段门禁包含 `-Backend` | Maven 验证耗时较长 | 按实际需要调整门禁参数 |

## 6. 后续行动

- 后续可用 `harness-cli run -Feature F-00X` 驱动真实 feature。
- 如要全自动团队协作，下一步接 CI/Git hook，再演进为工作流引擎。

## 7. 首次运行卡死修复（2026-08-06 补充）

首次运行 `harness run -Feature F-001` 只显示 `stage analysis started` 后无输出的根因与修复：

- 任务卡模板要求 Codex 自己执行门禁命令，非交互模式触发命令审批后一直等待，表现为“卡住”。
- `codex` npm 启动器对 stdin 管道支持不稳定，`codex exec -` 收不到 prompt；已改为把任务卡内容作为参数传入。
- 执行器退出码原先会被控制台输出污染成数组，导致“实际成功但被判失败”；已改为只回传整数退出码。
- 门禁输出原先也会污染退出码；已改为正常显示输出但只返回整数退出码。
- 执行器新增 `-TimeoutSeconds`（默认 900 秒）与开始/结束提示，CLI 会打印日志路径，避免看起来“没了”。
- 执行器增加每 15 秒心跳输出（运行秒数 + 日志大小），长时间阶段也能看到进度。
- 任务卡明确“当前目录非 Git 仓库，不要执行 git 命令”，避免 coding 阶段反复触发 git 报错。

修改文件：`.harness/templates/pipeline-task-card.md.template`、`script/lib/codex-executor.ps1`、`script/harness-cli.ps1`。
