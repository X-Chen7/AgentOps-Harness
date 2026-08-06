# .harness/rules/project-structure.md

## 1. 文件定位

本文件定义示例后端后端工程的目录结构识别规则。

## 2. 标准目录地图

| 目录 | 职责 |
| --- | --- |
| `app-dependencies/` | 统一依赖版本和 BOM |
| `app-framework/` | Starter、公共能力、横切逻辑 |
| `app-server/` | 启动、装配、配置、打包 |
| `app-module-*/` | 后端业务模块 |
| `sql/` | 数据库脚本 |
| `script/` | 辅助脚本 |
| `.harness/` | Harness Engineering 规则、技能、知识和计划 |

## 3. 启用模块识别

后端启用模块以根 `pom.xml` 的 `<modules>` 为准。

被注释、未列入 `<modules>`、或仅保留目录的模块，不默认视为当前主线。

## 4. 服务装配识别

服务实际运行模块以 `app-server/pom.xml` 中依赖的 `*-biz` 为准。

一个业务模块进入当前运行链路，至少需要同时满足：

1. 根 `pom.xml` 启用；
2. `app-server/pom.xml` 装配；
3. 对应 Spring Bean 和配置未被禁用。

## 5. 未启用模块处理

未启用模块默认不修改。除非用户明确要求，智能体不得在未启用模块中扩展业务。

## 6. 自定义业务模块

自定义业务模块应遵循 `app-module-xxx/xxx-api` 与 `app-module-xxx/xxx-biz` 分层。

业务逻辑优先落在对应 `biz` 模块，跨模块接口放在 `api` 模块。

## 7. 智能体检查清单

任务开始前必须检查：

- 根 `pom.xml`；
- `app-server/pom.xml`；
- 目标模块目录；
- 相关配置文件；
- `ARCHITECTURE.md` 中的当前项目实例化说明。

## 8. 维护规则

模块启用关系、服务装配关系、目录职责变化时，必须同步更新 `ARCHITECTURE.md` 和本规则。
