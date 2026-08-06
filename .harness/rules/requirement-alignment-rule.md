# .harness/rules/requirement-alignment-rule.md

## 1. 文件定位

本文档定义复杂需求在进入方案设计、执行计划和编码前的需求对齐规则。

目标是避免只依据当前原型、局部代码或已有实现做方案，导致设计偏离需求文档和系统最终目标。

本规则适用于涉及以下内容的后端任务：

- 登录、SSO、OAuth2、Token、Client Credentials、PKCE；
- 用户、组织、部门、岗位、角色、菜单、资源、数据权限、字段权限；
- 开放 API、API 订阅、外部组织接入、API Key/Secret、签名验签；
- 跨服务边界、跨仓库协作、平台底座能力；
- L3 / L4 复杂度功能设计、执行计划和 Harness 文档修订。

## 2. 强制对齐原则

复杂需求必须先对齐需求文档，再对齐当前代码，最后确定最小改造方案。

处理顺序固定为：

1. 明确需求来源章节。
2. 识别系统最终目标。
3. 提炼业务能力边界。
4. 核对当前代码和 Harness 文档现状。
5. 判断哪些能力复用示例后端原框架。
6. 判断哪些能力由 `app-module-app-core` 扩展。
7. 判断哪些能力不应进入 `agentops-harness`。
8. 输出设计纠偏或落地方案。
9. 建立或更新执行计划。
10. 方案确认后再编码。

不得只根据前端原型、当前页面、已有表结构或已有接口倒推需求。

## 3. 需求章节引用要求

涉及目标业务系统核心能力时，方案和执行计划必须显式列出需求章节来源。

当前 RBAC/OAuth2 相关任务至少需要核对：

- `3.7.8 安全管理中心`：IAM、用户、角色、权限、密码策略、会话、2FA、敏感数据、审计、合规；
- `3.8 对外开放API系统`：API 服务发布、订阅授权、调用统计、服务组、发布者、订阅者、凭证、限流、签名验签；
- `3.8.5 系统管理模块`：权限管控、组织、用户、用户组、访问日志、操作日志；
- `3.9 移动端服务应用`：移动端登录注册、企业实名认证、子账号、角色分配、安全设置；
- `6 外部接口对接`：统一网关、多协议、多格式、OAuth2/JWT、API Key/Secret、RBAC、接口级和字段级权限；
- `6.1.3 订阅服务`：API 订阅申请、接口勾选、字段权限需求、审核、凭证发放、最小必要开放；
- `6.1.4 数据加密和身份认证机制`：传输加密、身份认证、多因素认证、审计和监控。

如果实际使用的需求文档章节编号发生变化，必须在设计说明中记录实际章节标题和引用位置。

## 4. 当前代码复用判断

基于示例后端后端框架的最小改造原则：

| 能力 | 默认处理方式 |
| --- | --- |
| 管理平台用户 | 复用 `system_users` |
| 平台后台角色 | 复用 `system_role` |
| 平台后台菜单 | 复用 `system_menu` |
| 平台内部部门 | 复用 `system_dept` |
| 岗位 | 复用 `system_post` |
| 文件和附件 | 复用 `app-module-infra` 文件能力 |
| OAuth2 客户端和 Token 主链路 | 复用 `system_oauth2_client` 和系统 OAuth2 能力 |
| 业务组织 | 使用 `app_core_org` 扩展，不直接等同 `system_dept` |
| 用户组织身份 | 使用 `app_core_user_org` 扩展 |
| 业务应用资源目录 | 使用 `app_core_resource` 扩展，不塞入 `system_menu` |
| 业务数据权限 | 使用 `app_core_data_scope_policy` 扩展 |
| 字段权限 | 使用 `app_core_field_policy` 扩展 |
| API 订阅授权 | 使用 `app_core_subscription` 或归属业务服务的订阅模型，按服务边界判定 |

复用不等于直接改原表语义。凡是会改变示例后端原生能力语义的设计，必须先提出替代方案。

## 5. 设计纠偏触发条件

出现以下任一情况，必须暂停编码并先输出纠偏方案：

- 需求文档与当前 Harness 设计不一致；
- 当前原型与需求文档不一致；
- 当前实现只能完成最小闭环，但不能满足需求验收；
- 权限模型混淆了管理后台菜单和业务应用资源；
- 把业务组织误建模为示例后端部门；
- 把 OAuth2 Client 当成业务权限主体；
- 让运营人员手工输入权限编码、字段编码或接口编码；
- 计划中的模块归属与四服务边界冲突；
- 需要修改 `app-framework` 或重写示例后端核心能力。

纠偏方案必须说明：

- 错误理解是什么；
- 正确需求依据是什么；
- 当前代码事实是什么；
- 哪些已有文档需要调整；
- 新方案如何做到最小改动和最大复用；
- 后续执行计划如何衔接已有 active/completed 计划。

## 6. 输出格式要求

L3 / L4 需求分析输出必须包含：

- 需求章节来源；
- 系统最终目标；
- 当前代码现状；
- 当前 Harness 文档现状；
- 可复用示例后端能力；
- `app-core` 需要新增或调整的能力；
- 不应修改或不应承载的能力；
- 模块边界；
- 数据模型边界；
- 权限模型边界；
- 前端配置方式；
- 兼容和迁移策略；
- 风险和待确认点；
- 是否需要更新设计说明、详细落地方案、执行计划、技术债。

## 7. 与其他 Harness 文档的关系

- `AGENTS.md` 只索引本规则，不承载具体纠偏结论。
- `.harness/rules/development-flow.md` 负责流程入口，本规则负责需求对齐细则。
- `.harness/rules/documentation-change-rule.md` 负责文档同步要求，本规则负责判断何时必须重审需求。
- `.harness/skills/request-analysis/SKILL.md` 必须按本规则输出复杂需求分析。
- `.harness/skills/cross-border-platform-implementation/SKILL.md` 必须按本规则判断四服务边界。
- `.harness/wiki/feature-design/` 中的 L3 / L4 设计说明必须引用本规则。

## 8. 当前阶段结论

`app-core` RBAC/OAuth2 后续修订必须先按本规则重新对齐需求文档，再调整：

- `.harness/wiki/feature-design/`
- `.harness/wiki/feature-design/`
- `.harness/wiki/data-model.md`
- `.harness/wiki/api-contract.md`
- `.harness/wiki/frontend-integration.md`
- `.harness/changes/active/`

