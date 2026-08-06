# Harness Skills V2

本目录是当前项目的智能体技能库。`SKILL.md` 是技能唯一权威，V1 的 `-spec.md` 草案已归档，不再参与日常维护。

## 目录结构

```text
.harness/skills/
├── README.md
├── SKILL-TEMPLATE.md
├── request-analysis/
├── coding-skill/
├── frontend-backend-integration/
├── expert-reviewer/
├── unit-test-write/
├── unit-test-ci/
├── db-schema-sync/
└── deploy-verify/
```

## 任务路由

按任务类型选择技能，再读取对应 `SKILL.md` 执行。

| 任务类型 | 使用技能 |
| --- | --- |
| 复杂需求、新功能、L3/L4、影响范围判断 | `request-analysis` |
| 明确的小范围后端代码修改 | `coding-skill` |
| 后端接口变更、前端对接、联调、联合验收 | `frontend-backend-integration` |
| 变更交付前 Review | `expert-reviewer` |
| 为后端变更补充测试 | `unit-test-write` |
| 执行最小验证、测试、打包、失败归因 | `unit-test-ci` |
| SQL、DO、Mapper、数据模型一致性检查 | `db-schema-sync` |
| 模块装配、配置、打包、部署前检查 | `deploy-verify` |

## 使用方式

1. 先读 `AGENTS.md`，确认任务路由和边界。
2. 按上表选择技能，打开对应 `SKILL.md`。
3. 涉及接口变化时，先使用 `frontend-backend-integration` 对齐契约。
4. 修改完成后使用 `unit-test-ci` 验证，使用 `expert-reviewer` 做交付前 Review。

## 安装说明

如需安装到 Codex，把每个技能目录复制到 Codex 的技能目录，例如 `~/.codex/skills/request-analysis/`。

## 维护规则

- 新增技能必须使用 `SKILL-TEMPLATE.md`。
- 技能目录保持一级平铺结构，禁止再出现 `skills/skills/` 嵌套。
- `SKILL.md` 是唯一权威，不新增 `*-spec.md` 草案。
- 每个技能必须包含触发条件、输入上下文、执行步骤、输出格式、停止条件和验证要求。
