---
name: db-schema-sync
description: 用于检查 SQL、DO、Mapper、VO/DTO、初始化数据、枚举注释和数据模型文档是否同步。当新增或修改表字段、修改 DO/Mapper/SQL，或需要数据模型一致性检查时使用。
---

# DB Schema Sync

## 定位

检查数据库模型与 Java 代码、接口文档和初始化数据是否一致，避免只改一处造成模型漂移。

## 触发条件

- 新增或修改表字段。
- 修改 DO。
- 修改 Mapper、XML 或 VO/DTO。
- 修改初始化数据或迁移脚本。
- 修改 `data-model.md` 或接口文档中的字段语义。

## 输入上下文

- SQL 脚本。
- DO、Mapper、VO/DTO。
- 初始化数据。
- `.harness/wiki/data-model.md`。
- `.harness/rules/sql-and-migration.md`。

## 检查步骤

1. 找到涉及的表。
2. 对比 SQL 字段和 DO 字段。
3. 检查 Mapper 和 XML 是否引用旧字段。
4. 检查 VO/DTO 是否受影响。
5. 检查初始化数据。
6. 检查字段注释和枚举注释：
   - SQL 字段 `COMMENT`。
   - DO 字段中文注释。
   - 枚举值 key-value 映射。
7. 检查 `data-model.md` 是否需要更新。
8. 检查是否需要迁移脚本和回滚脚本。

## 输出格式

```text
涉及表：
涉及字段：
已同步：
未同步：
枚举/注释风险：
建议验证：
```

## 停止条件

- 涉及删除字段、删表、批量数据修复。
- 字段业务含义不明确。
- MySQL/KingbaseES 类型差异无法判断。

## 验证要求

至少执行受影响模块编译或测试；SQL 兼容性无法验证时必须说明。
