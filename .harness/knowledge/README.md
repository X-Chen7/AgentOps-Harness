# 知识库检索化

本目录把 Markdown 知识升级为机器可读索引 + 结构化事实 + 定点检索：

- `index.json`：由 `harness knowledge index` 生成的统一知识索引，提交到 Git。
- `api/`：接口事实，YAML 结构，`harness knowledge api <路径|名称>` 精确查询。
- `schema/`：表结构事实，YAML 结构，`harness knowledge table <表名>` 精确查询。

常用命令：

```bash
python -m harness knowledge index
python -m harness knowledge route "前端联调接口怎么做"
python -m harness knowledge get <entry-id>
python -m harness knowledge api /oauth2/token
python -m harness knowledge table platform_core_org
python -m harness knowledge check
python -m harness knowledge bench --save / --compare
python -m harness knowledge extract --controllers <dir> --sql <dir>
```

维护规则：

- 索引必须用 `harness knowledge index` 重建，禁止手改 `index.json`。
- 新知识文件加入 `.harness/rules/`、`.harness/wiki/` 或结构化目录后必须重新建索引。
- `api/`、`schema/` 文件是结构化事实源，字段含义保持稳定。
- `harness check` 会强制校验索引新鲜度、覆盖率和断链。
