# Harness 架构优化完成记录

## 1. 完成摘要

- 完成日期：2026-08-05
- 执行人：Codex
- 关联计划：`.harness/README.md`、`script/harness-check.ps1`
- 当前结论：`.harness` 已按优先级完成收敛修复，入口路径、新旧规范、变更记录和生成物边界已统一。

## 2. 原始目标

- 参考优秀开源 harness 形态，按已确认计划优化 `.harness` 架构。
- 不改业务代码，不引入新依赖，保持现有五支柱结构。

## 3. 实际改动

| 类型 | 改动说明 |
| --- | --- |
| 技能目录 | `.harness/skills/skills/*` 摊平为 `.harness/skills/*`，合并 README 为任务路由表 |
| 入口索引 | `AGENTS.md` 补充 `frontend-backend-integration` 技能路由和 `.harness/README.md` 索引 |
| 旧规范 | 17 个 `-spec.md` 及根目录 `agents-map-spec.md`、`architecture-spec.md` 归档到 `.harness/archive/v1-specs/` |
| 变更记录 | 已完成计划移入 `changes/completed/archive/`；67KB 跟踪文档拆为状态索引 + 23 个按日期归档记录 |
| 技术债 | 主清单只保留未关闭条目，TD-0003 补入已关闭记录 |
| 生成物 | `.harness/.zread` 移出到 `docs/zread/harness/.zread`，删除 `.obsidian`，`.gitignore` 忽略 zread |
| 目录索引 | 新增 `.harness/README.md` 和归档区说明 |
| 校验 | 新增 `script/harness-check.ps1`，检查 AGENTS 路径、技能结构、active 状态、spec 草稿、zread 位置、技术债状态和归档链接 |

## 4. 验证结果

| 验证项 | 命令或方式 | 结果 |
| --- | --- | --- |
| Harness 健康检查 | `powershell -NoProfile -ExecutionPolicy Bypass -File script\harness-check.ps1` | 通过，0 error |
| 大文档预警 | 同上 | 2 warning：`应用核心RBAC与OAuth2前端对接说明.md` 51.9KB、`应用核心RBAC与OAuth2实施方案.md` 45.6KB |

## 5. 决策记录

- 采用“归档不删除”处理 V1 spec 草稿，保留历史决策。
- `.zread` 作为生成物只读参考，不写入手写维护体系。
- 不批量改名现有英文计划文件，只在模板中固化后续中文命名规则。

## 6. 遗留风险

| 风险 | 影响 | 建议处理 |
| --- | --- | --- |
| 两份 wiki 文档超过 40KB | 后续维护和检索成本较高 | 按专题拆分或改为生成式接口清单 |
| 根目录 `.zread` 仍存在 | 属于生成物，可能过期 | 按需重新生成，不作为权威来源 |

## 7. 后续行动

- 后续每次修改 Harness 后运行 `script/harness-check.ps1`。
- 新增技能使用 `.harness/skills/SKILL-TEMPLATE.md`。
- 计划完成时移入 `changes/completed/archive/`，不再长期停留在 `active/`。
