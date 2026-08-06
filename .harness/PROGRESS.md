# Harness 进度（PROGRESS）

> 每次会话结束必须更新本文件。新会话开始时先读本文件，再读 `changes/active/feature-list.json`。

## 当前状态

- 更新日期：2026-08-07
- 当前任务：F-009 流水线状态一致性校验
- 当前状态：`todo`
- 最近验证：`script/check.ps1` 待 F-009 落地后通过

## 已完成

- Harness 第一轮收敛：技能扩平、spec 归档、changes 生命周期、wiki 隔离、校验脚本。
- Harness 第二轮状态与反馈优化：PROGRESS、feature-list、check.ps1、模板和工具边界。
- Harness 第三轮 changes 团队协作 Git 同步增强：Git 规则、feature 字段、校验脚本、同步脚本、hooks、模板、完成索引和记录。
- Harness 第四轮 Codex 原生对齐：.codex/skills 技能同步、项目级 Codex 配置、AGENTS 模块化、模块级 AGENTS、模板与基准、harness-check 扩展。
- Harness 第五轮 AI 自动加载范围固化：AGENTS.d/00-common.md 和 .harness/README.md 写明自动加载/按需读取边界。
- Harness 第六轮按需读取判定固化：AGENTS.d/00-common.md 增加“何时必须读取”判定表。
- Harness 第七轮可执行流水线（F-007）：harness-cli.ps1 + codex-executor.ps1 + pipelines/default.json + 任务卡/报告模板 + state/ + 交互菜单 harness.cmd 落地，check.ps1 通过；后续退役，由 Codex 桌面版多智能体编排取代，运行器归档至 .harness/archive/harness-cli/。
- Harness 第八轮 Codex 桌面版迁移：新增 5 个桌面版角色契约、script/harness-git.ps1 独立 Git/PR 自动化，编排交由桌面版多智能体接管。
- Harness 第九轮 Codex 桌面版可执行多智能体流水线 v2（F-008）：落地 desktop-pipeline.json、状态 schema、handoff 协议、角色升级、门禁/重试/打回/升级语义和校验脚本。

## 进行中

- [ ] F-009 流水线状态一致性校验：让 `script/harness-check.ps1` 在流水线状态为 `done` / `blocked` 时校验 feature-list 的 `pipeline.status` 一致，并完整走一遍 Git/PR 链路。

## 下一步

- 按 F-009 计划实现并验证，再执行 `harness commit -Feature F-009`。
- 配置 remote 后执行 `harness push -Feature F-009` 和 `harness pr -Feature F-009`。
- 每次会话结束运行 `script/check.ps1` 并回填结果。
- 同步更新 `changes/active/feature-list.json` 中的状态。

## 决策记录

- WIP=1：同一时间只允许一个 `in_progress` 功能。
- 功能状态以 `changes/active/feature-list.json` 为机器可读权威。
- feature 状态与 Git 绑定：`committed` / `pushed` / `merged` 必须回写 commit、branch、push_status。
- 完成记录必须同步维护 `changes/completed/INDEX.md`。
- 完成判定必须经过 `script/check.ps1` 和 `expert-reviewer`，不能由执行者自报完成。
