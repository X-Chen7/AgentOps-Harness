# owner.md

## 1. 文件定位

本文件定义当前示例后端后端项目的责任人、角色职责、审批边界和风险升级路径。

本文件不记录账号、密码、密钥、私人联系方式，不承载业务设计、编码规范或执行计划。

当前示例项目暂无真实责任人，责任人字段先保留为 `待补充`。

## 2. 项目责任人

| 角色 | 负责人 / 团队 | 说明 |
| --- | --- | --- |
| Product Owner | 待补充 | 负责业务目标、需求范围、验收标准 |
| Tech Owner | 待补充 | 负责技术方案、模块边界、关键技术决策 |
| Backend Owner | 待补充 | 负责后端业务实现和测试 |
| Framework Owner | 待补充 | 负责 `app-framework` 和公共能力 |
| Server Owner | 待补充 | 负责 `app-server`、启动配置和模块装配 |
| Database Owner | 待补充 | 负责 SQL、表结构、初始化数据和迁移 |
| Security Owner | 待补充 | 负责认证、授权、租户、数据权限和密钥风险 |
| Release Owner | 待补充 | 负责打包、部署、发布和回滚 |
| Agent Operator | 待补充 | 负责使用智能体执行任务并确认结果 |

## 3. 角色职责

### Product Owner

- 确认需求是否进入当前迭代；
- 确认业务验收标准；
- 确认接口行为变化是否符合业务预期。

### Tech Owner

- 确认跨模块设计；
- 确认是否修改框架层；
- 确认关键依赖、架构和公共能力变更。

### Backend Owner

- 确认 Controller、Service、Mapper、DO、VO、测试改动；
- 审查后端业务逻辑；
- 确认最小验证范围。

### Framework Owner

- 确认 `app-framework`、Starter、公共工具和横切能力变更；
- 确认框架层改动是否应下沉到业务模块；
- 审查可能影响多个模块的公共逻辑。

### Server Owner

- 确认 `app-server` 启动、配置、打包和模块装配变更；
- 确认环境配置是否符合当前项目运行要求；
- 确认服务启动链路和依赖装配是否正确。

### Database Owner

- 确认表结构、初始化数据、迁移和回滚；
- 审查高风险 SQL；
- 确认 MySQL / KingbaseES 兼容性要求。

### Security Owner

- 确认认证、授权、OAuth2、Token、租户、数据权限相关变更；
- 审查密钥、配置、安全策略风险。

### Release Owner

- 确认打包、部署、发布和回滚方案；
- 确认发布前验证结果；
- 确认上线窗口和回退路径。

### Agent Operator

- 使用智能体执行开发、排查、文档和验证任务；
- 确认智能体输出是否符合任务目标；
- 在发现高风险变更时推动人工确认。

## 4. 通用审批矩阵

通用审批矩阵适用于所有基于示例后端后端框架的项目。

| 变更类型 | 智能体是否可直接推进 | 需要确认 |
| --- | --- | --- |
| 小范围 Bug 修复 | 可以 | Backend Owner 事后 Review |
| Controller / Service 小范围改动 | 可以 | Backend Owner 事后 Review |
| 新增接口 | 需要确认 | Product Owner、Backend Owner |
| 修改接口请求或响应结构 | 需要确认 | Product Owner、Backend Owner |
| 登录 / OAuth2 / Token 改动 | 需要确认 | Tech Owner、Security Owner |
| 租户 / 数据权限改动 | 需要确认 | Tech Owner、Security Owner |
| SQL 表结构变更 | 需要确认 | Database Owner、Backend Owner |
| 初始化数据变更 | 需要确认 | Database Owner、Product Owner |
| 删除字段、删表、批量数据修复 | 必须暂停 | Database Owner、Tech Owner |
| `app-framework` 改动 | 必须暂停 | Framework Owner、Tech Owner |
| `app-server` 装配改动 | 需要确认 | Server Owner、Tech Owner |
| 依赖版本升级 | 必须暂停 | Tech Owner、Release Owner |
| 安全配置和密钥策略变更 | 必须暂停 | Security Owner、Tech Owner |
| 大范围重构 | 必须暂停 | Tech Owner |
| 文档索引修正 | 可以 | Agent Operator 事后确认 |

## 5. 当前项目审批矩阵

当前示例项目在通用审批矩阵基础上追加以下要求：

| 变更类型 | 智能体是否可直接推进 | 需要确认 |
| --- | --- | --- |
| `/api/auth/login` 登录接口行为变化 | 需要确认 | Backend Owner、Security Owner |
| OAuth2 客户端校验逻辑变化 | 需要确认 | Tech Owner、Security Owner |
| 授权码生成、校验、过期策略变化 | 需要确认 | Tech Owner、Security Owner |
| Access Token / Refresh Token 生成和刷新策略变化 | 必须暂停 | Tech Owner、Security Owner |
| `redirect_uri` 校验规则变化 | 必须暂停 | Tech Owner、Security Owner |
| 租户上下文和用户权限上下文变化 | 必须暂停 | Tech Owner、Security Owner |
| SSO 初始化 SQL 数据变化 | 需要确认 | Database Owner、Backend Owner |
| OAuth2 客户端初始化数据变化 | 需要确认 | Product Owner、Database Owner、Security Owner |
| `app-server` OAuth2 / Security 相关配置变化 | 需要确认 | Server Owner、Security Owner |

## 6. 智能体可自主推进范围

智能体可以在边界清楚、影响范围小、且不涉及破坏性变更时直接推进：

- 代码阅读和上下文整理；
- 小范围 Bug 修复；
- 局部测试补充；
- 局部文档修正；
- 只读索引生成；
- 最小验证执行；
- 执行计划草案整理。

前提：

- 不修改未确认启用的模块；
- 不绕过认证、权限、租户、数据权限；
- 不删除用户已有改动；
- 不执行破坏性 Git 操作；
- 不引入未经确认的新依赖。

## 7. 必须人工确认范围

以下事项必须暂停并等待确认：

- 删除表、删除字段、批量数据修复；
- 修改登录、OAuth2、Token、租户、数据权限核心逻辑；
- 修改 `app-framework`；
- 修改根 `pom.xml` 模块启用关系；
- 修改 `app-server/pom.xml` 服务装配关系；
- 升级核心依赖；
- 引入新中间件；
- 修改生产配置、安全配置、密钥策略；
- 大范围重构、批量格式化、批量改名。

## 8. 冲突和风险升级路径

智能体遇到冲突或高风险变更时，应：

1. 停止修改；
2. 描述已发现事实；
3. 标明涉及文件和影响范围；
4. 给出可选方案；
5. 等待人工确认。

典型触发条件：

- 当前分支存在未解释的同文件改动；
- 需求与现有架构冲突；
- 需求需要跨模块修改；
- 修改会影响登录、权限、租户、Token、SQL 数据；
- 测试失败但失败原因不确定；
- 文档与代码事实不一致。

## 9. 维护规则

- 项目责任人变化时更新本文件；
- 审批边界变化时更新本文件；
- 新增高风险变更类型时更新审批矩阵；
- 当前项目审批矩阵变化时更新本文件；
- 本文件不得记录敏感凭据和私人联系方式。
