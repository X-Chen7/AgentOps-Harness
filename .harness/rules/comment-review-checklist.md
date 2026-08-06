# .harness/rules/comment-review-checklist.md

## 1. 文件定位

本文档用于约束后端开发中的注释专项检查，避免新增或迭代代码时遗漏中文注释。

本文档不替代 `coding-standard.md` 和 `development-flow.md`，而是作为交付前和 Review 时的执行清单。

## 2. 适用范围

以下改动默认需要执行本清单：

- 新增 `public` / `protected` 方法。
- 修改已有 `public` / `protected` 方法实现。
- 涉及权限、租户、OAuth2、Token、状态流转、组织绑定、审计的业务方法。
- 新增或修改 DO / VO 字段。
- 多文件联动或复杂逻辑迭代任务。

## 3. 必查项

### 3.1 方法注释

- 新增的 `public` / `protected` 方法是否存在中文 Javadoc。
- 注释是否说明方法用途。
- 注释是否说明关键参数含义。
- 注释是否说明返回值语义。
- 有副作用的方法是否说明副作用。
- 涉及权限、租户、组织、OAuth2、Token 的方法是否说明关键约束。
- 修改过的方法，注释是否仍与当前实现一致。

### 3.2 DO / VO 注释

- DO 类是否有中文类注释。
- DO 字段是否有中文注释。
- VO 类是否有中文类注释。
- 请求字段和响应字段是否有清晰中文说明。
- 新增字段是否同步补充注释。

### 3.3 Mapper / Enum 注释

- Mapper 默认查询方法是否说明查询条件和返回语义。
- 错误码、状态码、业务常量是否有必要中文说明。
- 是否存在新增枚举或错误码但无语义说明的情况。

### 3.4 枚举 / 常量专项检查

- 新增稳定值集合是否优先使用枚举，而不是一组数字常量。
- 新增 `private static final` 常量是否有中文注释。
- 字符串格式模板常量是否说明模板含义。
- `targetType`、资源类型、主体类型、审计对象类型等协议型稳定值是否复用统一枚举，而不是散落魔法字符串。
- 是否存在“本应复用枚举，却在类内重复定义状态 / 类型常量”的情况。
- 涉及接口协议、SQL 字段、权限编码、审计结果的常量是否能从注释直接看懂语义。

## 4. 快速扫描命令

提交前可使用以下命令做快速扫描：

```bash
rg "public .*\\(" app-module-*/src/main/java
rg "protected .*\\(" app-module-*/src/main/java
rg "private static final" app-module-*/src/main/java
```

说明：

- `public` / `protected` 方法命中后，需要人工检查方法前是否存在 Javadoc。
- `private` 方法不要求全部写注释，但复杂私有方法仍需人工判断是否需要说明。
- `private static final` 命中后，需要人工检查是否缺少中文注释、是否误用常量替代枚举。

## 5. 交付前结论规则

注释专项检查必须给出明确结论：

- `已符合注释规范`
- `存在注释遗漏`
- `存在注释与实现不一致`

不得用“功能没问题”替代注释结论。

## 6. Review 口径

满足以下任一情况，Review 应要求补充后再交付：

- 新增 `public` / `protected` 方法无中文 Javadoc。
- 方法职责已改但注释未更新。
- DO / VO 新增字段无中文说明。
- 注释与实现明显不一致。
- 高风险业务方法缺少关键约束说明。

## 7. 字段权限与敏感字段检查

- 响应中新增手机号、邮箱、姓名、证件号、银行账户、密钥、客户商业秘密等字段时，必须评估字段权限策略和 `sensitivity_level`。
- `sensitivity_level` 取值必须与 `PlatformSensitiveFieldLevelEnum`、SQL 注释、DO/VO 注释和前端对接说明一致。
- `sensitivity_level >= 3` 的字段接口必须检查是否需要 `@PlatformFieldPermissionResource`。
- 字段访问审计不得记录字段原始敏感值。
