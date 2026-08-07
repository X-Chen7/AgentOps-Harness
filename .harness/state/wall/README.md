# 便签墙（sticky wall）

本目录存放流水线运行期的共享便签，不提交 Git。

- 文件名：`<feature>.md`
- 模板：`.harness/templates/sticky-wall.md.template`
- 规则：阶段 Agent 只追加便签，不修改或删除已有便签；协调者可以关闭便签。
- 便签类型：`decision` / `risk` / `question` / `fact`

便签墙用于跨阶段传递决策、风险、待确认项和事实，避免多 Agent 上下文丢失。
