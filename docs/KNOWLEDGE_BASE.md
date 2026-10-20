# 知识库维护

当前知识资料在 `data/` 目录下分两类：结构化非遗项目记录，以及用于路线、研学、创作的补充文档。两者都可检索，但仅来源核对过的项目资料可以作为相应名录事实的依据。

## 项目记录

`data/heritage_records.json` 当前有 12 条记录，分别保存项目名称、别名、城市、类别、名录编号、来源链接、核对日期和文化事实。`audiences`、`experience`、`notice` 则是产品编辑的适用人群、体验建议和出行提醒，不代表官方实际活动安排。

| 字段 | 用途 |
| --- | --- |
| `id` / `name` / `aliases` | 项目标识、名称和别名 |
| `cities` / `category` | 城市与类别 |
| `registry_code` | 经核对的名录编号 |
| `source_name` / `source_url` | 机构与对应项目页面 |
| `verified_on` | 本仓库核对资料的日期 |
| `facts` | 经过整理的文化事实 |
| `audiences` / `experience` / `notice` | 使用建议和注意事项 |

来源要能明确对应到所写项目。不能仅凭名称推断项目编号、历史人物或活动地点。例如，**龙舟说唱**属于曲艺，不应被当作水上龙舟竞渡；两者名称相近但不是同一种活动。

## 辅助资料

`data/` 下的 Markdown、TXT 用于城市路线、研学和内容创作。Markdown 可以附带元数据：

```yaml
---
title: 粤剧文化观察
city: 广州
category: 传统戏剧
source_name: 资料来源名称
source_url: https://example.com/project-page
---
```

示例 URL 仅用于说明字段；正式资料应填写实际核对过的具体页面。无来源时不要虚构链接或名录信息。尽量用自己的文字概括资料，避免复制大段原文。

## 更新流程

新增或修改项目时，先检查具体项目页面及其字段，再同步修改 `backend/data/` 中的部署镜像。增加评测案例后运行：

```bash
python -m scripts.run_benchmark
pytest
```

检索结果不包含实时场馆开放、票价、演出和预约信息；这些数据应让使用者在出行前确认。
