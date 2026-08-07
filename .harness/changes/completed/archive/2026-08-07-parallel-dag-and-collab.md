# 执行计划：可执行多智能体流水线增强（F-010）

> 状态：执行中
> 目标 Feature：F-010

## 目标

在现有串行 DAG 基础上落地：

1. 基于 `depends_on` 的并行阶段执行（拓扑批次推进）。
2. 写权协调：并行阶段 `write_scope` 重叠时禁止并行并降级串行。
3. 便签墙：共享决策、风险、待确认便签，只追加不覆盖。
4. debate 轻量版：评审分歧时发起一轮双评审人辩论并裁决。

## 验收标准

1. 状态 schema 升级到 `1.1`，支持 `active_stages`。
2. 并行示例配置 `analysis -> coding-a/coding-b -> test -> review` 可通过校验。
3. 并行阶段 `write_scope` 重叠被 `harness-check` 拦截。
4. 便签墙模板与 wall 目录说明存在，协调协议引用。
5. debate 字段与一轮辩论流程写入评审契约和协调协议。
6. `script/check.ps1` 0 error，负向验证通过。

## 影响文件

- `.harness/pipelines/desktop-pipeline.json` / `desktop-pipeline.parallel.example.json`
- `.harness/pipelines/desktop-coordinator.md`
- `.harness/templates/pipeline-state.example.json` / `sticky-wall.md.template` / `pipeline-handoff.md.template`
- `.harness/state/README.md` / `.harness/state/wall/README.md`
- `.harness/agents/pipeline/README.md` / `reviewer.md` / `debater.md`
- `script/harness-check.ps1`
- `feature-list` / `PROGRESS` / 完成记录

## 门禁

```powershell
script/check.ps1
```
