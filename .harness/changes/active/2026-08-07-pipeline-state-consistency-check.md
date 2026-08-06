# 执行计划：桌面流水线状态一致性校验（F-009）

> 状态：执行中
> 目标 Feature：F-009

## 目标

让 `script/harness-check.ps1` 在流水线状态文件为 `done` 或 `blocked` 时，校验 feature-list 的 `pipeline.status` 是否一致，避免“流水线跑完了但状态没回写”。

## 验收标准

1. 状态文件为 `done` 时，feature-list 的 `pipeline.status` 必须为 `done`。
2. 状态文件为 `blocked` 时，feature-list 的 `pipeline.status` 必须为 `blocked`。
3. 不存在状态文件时，不影响正常检查。
4. 负向验证：临时状态文件 `done` + feature-list `not_started` 会被拦截。

## 执行阶段

`analysis -> coding -> test -> review`

## 影响文件

- `script/harness-check.ps1`：新增一致性校验。
- 本计划、feature-list、PROGRESS、完成记录。

## 门禁

```powershell
script/check.ps1
```
