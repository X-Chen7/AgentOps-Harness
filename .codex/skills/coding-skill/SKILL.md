---
name: coding-skill
description: 用于示例后端后端项目中的明确小范围代码修改。当任务涉及 Controller、Service、Mapper、DO、VO、枚举、SQL 或配置修改，且边界清楚、需要最小改动并同步接口契约与文档时使用。
---

# Coding Skill

## 定位

按最小改动原则完成后端实现，保证代码、SQL、接口契约、前端对接说明和 Harness 文档同步。

## 触发条件

- 明确的 Bug 修复。
- 明确的接口或 Service 小改动。
- 明确的 SQL、配置或装配修正。
- 需求已经过 `request-analysis`，边界清晰。

## 输入上下文

- 需求分析结果。
- `AGENTS.md`、`ARCHITECTURE.md`。
- `.harness/rules/coding-standard.md`、`backend-module-boundary.md`、`sql-and-migration.md`。
- 相关代码、SQL、测试、`api-contract.md`、`frontend-integration.md`。

## 执行步骤

1. 确认目标模块已启用且属于当前主线。
2. 阅读相关 Controller、Service、Mapper、DO、VO、枚举、SQL 和测试。
3. 设计最小改动，避免无关重构和格式化。
4. 判断是否影响接口协议或前端：
   - 是：先更新 `api-contract.md` 和 `frontend-integration.md`，或调用 `frontend-backend-integration`。
   - 否：继续实现。
5. 修改代码，并同步补充方法、DO、VO、常量注释。
6. 同步 SQL、初始化数据、迁移脚本和数据模型文档。
7. 执行最小验证。
8. 输出交付说明。

## 输出格式

```text
修改点：
原因：
影响范围：
接口契约是否变化：
SQL/配置是否变化：
验证结果：
风险：
```

## 停止条件

- 需要修改框架层但未确认。
- 涉及删表、删字段、批量数据修复。
- 涉及登录、OAuth2、Token 核心策略。
- 接口契约或前端影响不明确。
- 测试失败且无法归因。

## 验证要求

按影响范围选择最小验证命令；无法验证时说明原因。
