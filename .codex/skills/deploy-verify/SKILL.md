---
name: deploy-verify
description: 用于启动、配置、模块装配、依赖、打包和部署前检查，输出配置风险和验证结论。当修改 app-server、配置、依赖、模块装配，或发布前需要检查时使用。
---

# Deploy Verify

## 定位

在打包和部署前检查服务装配、配置、依赖和运行风险，避免把“能编译”当成“能部署”。

## 触发条件

- 修改 `app-server`。
- 修改配置文件。
- 修改依赖或模块装配。
- 发布前检查或打包失败排查。

## 输入上下文

- `app-server/pom.xml`。
- `application-*.yaml`。
- 根 `pom.xml`。
- Docker、脚本或部署说明。
- `.harness/wiki/runtime-and-deployment.md`。

## 检查步骤

1. 检查根 `pom.xml` 启用模块。
2. 检查 `app-server/pom.xml` 装配模块。
3. 检查当前 profile 是否正确。
4. 检查数据库、Redis、MQ、文件存储配置。
5. 检查密钥和敏感配置是否明文。
6. 检查前端代理、环境地址、CORS 和认证头透传。
7. 执行打包验证。
8. 记录未验证依赖。

## 常用命令

```bash
mvn -pl app-server -am package -DskipTests
```

## 输出格式

```text
检查范围：
执行命令：
验证结果：
配置风险：
未验证依赖：
建议下一步：
```

## 停止条件

- 涉及生产配置。
- 涉及密钥策略。
- 引入新中间件。
- 打包失败且原因不明。
- 需要真实环境才能验证。
