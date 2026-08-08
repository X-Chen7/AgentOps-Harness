# Harness 进度（PROGRESS）

> 每次会话结束必须更新本文件。新会话开始时先读本文件，再读 `changes/active/feature-list.json`。

## 当前状态

- 更新日期：2026-08-08
- 当前任务：F-015 问题跟踪 / PR 双向同步（已完成，direct 直写已启用）
- 当前状态：`merged`
- 最近验证：`python -m pytest -q` 82 passed；`harness check` 0 errors；`harness github sync --strict` up to date；`harness knowledge bench` 8/8；direct 直写闭环 F-017/F-018 已验证

## 已完成
- F-015 问题跟踪 / PR 双向同步：`harness github sync` 事件驱动同步、Issue/PR 状态回写、自动归档、`github-sync` CI 门禁落地；PR #12 合入，PR #20 完成传输层收尾，PR #24 增加直写路径白名单，PR #26 修复机器人凭据并迁移 main 到 ruleset，direct 直写模式已启用。
- F-016 双向同步自动生成验证：Issue #15 自动生成 feature/计划，关闭未合并后回写 `blocked`，验证自动同步闭环。
- F-017/F-018 direct 直写验证：Issue #25/#27 自动生成 feature 并直推 main，关闭未合并后自动回写 `blocked`，验证机器人直写闭环真实生效。

- Harness 第一轮收敛：技能扩平、spec 归档、changes 生命周期、wiki 隔离、校验脚本。
- Harness 第二轮状态与反馈优化：PROGRESS、feature-list、check.ps1、模板和工具边界。
- Harness 第三轮 changes 团队协作 Git 同步增强：Git 规则、feature 字段、校验脚本、同步脚本、hooks、模板、完成索引和记录。
- Harness 第四轮 Codex 原生对齐：.codex/skills 技能同步、项目级 Codex 配置、AGENTS 模块化、模块级 AGENTS、模板与基准、harness-check 扩展。
- Harness 第五轮 AI 自动加载范围固化：AGENTS.d/00-common.md 和 .harness/README.md 写明自动加载/按需读取边界。
- Harness 第六轮按需读取判定固化：AGENTS.d/00-common.md 增加“何时必须读取”判定表。
- Harness 第七轮可执行流水线（F-007）：harness-cli.ps1 + codex-executor.ps1 + pipelines/default.json + 任务卡/报告模板 + state/ + 交互菜单 harness.cmd 落地，check.ps1 通过；后续退役，由 Codex 桌面版多智能体编排取代，运行器归档至 .harness/archive/harness-cli/。
- Harness 第八轮 Codex 桌面版迁移：新增 5 个桌面版角色契约、script/harness-git.ps1 独立 Git/PR 自动化，编排交由桌面版多智能体接管。
- Harness 第九轮 Codex 桌面版可执行多智能体流水线 v2（F-008）：落地 desktop-pipeline.json、状态 schema、handoff 协议、角色升级、门禁/重试/打回/升级语义和校验脚本。
- F-009 流水线状态一致性校验：`script/harness-check.ps1` 在流水线状态为 `done` / `blocked` 时校验 feature-list 的 `pipeline.status` 一致，负向验证通过。
- F-009 Git/PR 链路收尾：`harness commit`、`harness push`、PR #1 创建与 squash 合并全部完成，feature-list 状态回写为 `merged`。
- F-010 可执行多智能体流水线增强：并行 DAG、写权仲裁、便签墙、debate 轻量版落地，schema 升级 1.1，负向验证通过。
- F-011 PowerShell 工具链迁移到 Python CLI：Python CLI、pytest 测试、GitHub Actions CI 落地，PowerShell 降级为兼容包装，PR #3 squash 合并完成。
- F-012 CI/CD 机器验收 + PR 门禁：`harness lint` / `dod` / `check --ci/--sql`、pre-commit/pre-push、GitHub Actions 五段检查、main 分支保护全部落地，PR #4 squash 合并完成。
- F-013 技能注册表 + 技能测试与评测：skill.yaml 契约、fixtures 场景库、`harness skill validate/test/bench/record/promote`、CI skills job 与分支保护落地，对抗式审查修复后 PR #5 squash 合并完成。
- F-014 知识库检索化：`harness knowledge index` 生成机器可读索引，`route/search/get/api/table` 定点检索，结构化 API/表事实与代码提取器，`check` 防过期防断链，`bench` 8 用例基线回归，CI knowledge job 落地，PR #8 squash 合并完成。

## 进行中


## 下一步

- 进一步加固：升级为 GitHub App，把 ruleset bypass actor 从用户账号换成 App 集成，并增加令牌到期提醒与轮换。
- 可选：清理验证用 Issue #25/#27 及 F-017/F-018 测试记录，保持仓库台账干净。
- 后续新 feature 继续按 `analysis -> coding -> test -> review -> Git/PR` 流程执行。
- 每次会话结束运行 `script/check.ps1` 并回填结果。
- 同步更新 `changes/active/feature-list.json` 中的状态。

## 决策记录

- WIP=1：同一时间只允许一个 `in_progress` 功能。
- 功能状态以 `changes/active/feature-list.json` 为机器可读权威。
- feature 状态与 Git 绑定：`committed` / `pushed` / `merged` 必须回写 commit、branch、push_status。
- 完成记录必须同步维护 `changes/completed/INDEX.md`。
- 完成判定必须经过 `script/check.ps1` 和 `expert-reviewer`，不能由执行者自报完成。
- GitHub 状态以 `feature-list.json` 为权威，Issue/PR 事件只触发重新计算，不直接改写台账。
- 已配置 fine-grained PAT + repository ruleset bypass；direct 模式只允许路径白名单内的 `.harness/**` 文件直写 main，代码改动仍必须走 PR。
