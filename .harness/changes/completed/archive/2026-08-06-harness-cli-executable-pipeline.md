# harness-cli 可执行流水线 v1 执行计划

## 1. 任务目标

- 目标：落地 `harness-cli` 可执行流水线，输入 feature/issue 后按 `需求分析 -> 编码 -> 测试 -> 评审` 顺序执行，每个阶段用脚本门禁验收，不通过不进入下一阶段。
- 非目标：不接 CI/Git hook；不自动 push；不修改业务代码。
- 成功标准：dry-run、状态、报告、重置命令可用；`script/check.ps1` 通过。

## 2. 背景

参考 gstack 多智能体编排、Claude Code subagents、Codex 多智能体模式，把 Harness 从“文档治理”升级为“可执行流程治理”。

## 3. 决策记录

- 1A：使用 PowerShell 实现，与现有脚本栈一致，零新依赖。
- 2A：使用 Codex CLI 适配器执行每个 Agent 阶段。
- 3A：使用 JSON 文件保存流水线状态。
- 4A：先做纯本地 CLI，不接 Git hook/CI。
- 5B：先落地 4 阶段闭环，Git/PR 作为可选第 5 阶段，默认关闭且不自动 push。

## 4. 文件清单

| 文件 | 内容 |
| --- | --- |
| `script/harness-cli.ps1` | 主命令：run/status/report/reset/stage |
| `harness.cmd` | 启动器：不带参数进入交互式菜单 |
| `script/lib/codex-executor.ps1` | Codex CLI 执行适配器 |
| `.harness/pipelines/default.json` | 流水线定义：阶段、提示词模板、门禁 |
| `.harness/templates/pipeline-task-card.md.template` | 阶段任务卡模板 |
| `.harness/templates/pipeline-report.md.template` | 流水线报告模板 |
| `.harness/state/` | 流水线状态、任务卡、日志、报告 |
| `.harness/changes/active/feature-list.json` | schema 1.2 + F-007 |
| `script/harness-check.ps1` | 流水线产物和状态校验 |

## 5. 验收标准

1. `harness-cli run -Feature F-001 -DryRun` 能打印全部阶段和门禁。
2. `harness.cmd` 不带参数能进入交互式菜单。
3. 每个阶段由 Codex 执行，门禁通过才进入下一阶段。
4. 门禁失败时状态标记 `blocked`，feature history 追加失败记录。
5. 中断后 `-Resume` 能从失败阶段继续。
6. `script/check.ps1` 通过。

## 6. 风险

- 真实 `codex exec` 尚未在流水线中做端到端实测，需要用户在本机验证一次完整运行。
- 当前目录不是 Git 仓库，Git/PR 阶段不可用。
