# 多智能体流水线角色

本目录定义 Codex 桌面版可执行多智能体流水线的角色契约。

## 流水线资产

- 配置：`.harness/pipelines/desktop-pipeline.json`
- 流程：`.harness/pipelines/desktop-coordinator.md`
- 状态：`.harness/state/pipeline-desktop-<feature>.json`
- 交接：`.harness/templates/pipeline-handoff.md.template`

## 角色

| 角色 | 文件 | 职责 |
| --- | --- | --- |
| 协调者 | `coordinator.md` | CEO/PM：推进阶段、跑门禁、处理重试/打回/升级、生成报告 |
| 需求分析 Agent | `analyst.md` | 只读分析，输出 scope 清单与影响范围 |
| 编码 Agent | `coder.md` | 唯一允许大范围写业务代码的角色 |
| 测试 Agent | `tester.md` | 补测试、跑测试，输出测试记录 |
| 评审 Agent | `reviewer.md` | 独立审查，输出 `pass` / `rework` / `needs_owner` |

## 执行顺序

`analysis -> coding -> test -> review`；

- `review` 打回时回到 `coding`，携带 `rework_scope`。
- 同一功能最多 `max_rework` 轮（当前配置为 2）。
- 门禁失败按 `max_attempts` 重试，超限升级 Owner。

## 写权矩阵

| 角色 | 可写 | 不可写 |
| --- | --- | --- |
| 协调者 | state、日志、报告、feature-list | 业务代码、SQL、配置、git push |
| 分析 Agent | 分析 handoff、scope 清单 | 业务代码、SQL、配置、测试 |
| 编码 Agent | scope 内业务代码、SQL、配置、测试 | scope 外文件、state、日志、git push |
| 测试 Agent | 测试文件、测试记录 | 业务逻辑、SQL、配置 |
| 评审 Agent | 评审报告 | 业务代码、测试、state |

## 协作规则

- 阶段 Agent 之间不直接沟通，产物通过 handoff 和 artifacts 传递。
- 每个阶段必须写独立 handoff，字段遵循模板。
- escalation 写在 handoff 的 `escalations` 字段，`blocking=true` 会暂停流水线。
- Git 提交、推送、PR 只由 `script/harness-git.ps1` 执行，且不自动 push。
