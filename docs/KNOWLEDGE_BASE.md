# 广东非遗知识库规范

`data/` 下的数据分为两类：**可追溯的结构化非遗项目**和**辅助场景资料**。两类数据均可参与检索，但官方出处与网站编辑建议应区别对待。

## 结构化官方项目

`data/heritage_records.json` 当前收录 12 条带精确国家级非遗项目页面的记录，`backend/data/heritage_records.json` 为 Vercel Service 部署镜像。

单条记录字段：

| 字段 | 内容 |
| --- | --- |
| `id`、`name`、`aliases` | 唯一标识、正式名称、常见别名 |
| `cities`、`category` | 地区与非遗类别 |
| `registry_code` | 已经核对的名录编号 |
| `source_name`、`source_url` | 来源单位与具体 HTTPS 项目页面 |
| `verified_on` | 本项目实际核验该页面的日期，而非官方发布日期 |
| `facts` | 可从可靠来源整理的项目文化事实 |
| `audiences`、`experience` | 网站提出的适用人群与体验建议，**不等于官方活动信息** |
| `notice` | 实际参访、课程、票务与演出需再确认的事项 |

新增记录前，先打开并核对来源页面。不得凭模型生成结果补充编号、人物、活动地点和核验日期；来源必须为明确项目页，不能把门户首页标成具体项目依据。增加条目后同步 `backend/data/`，补充对应的检索回归测试。

## Markdown / TXT 补充资料

`data/*.md` 与 `data/*.txt` 用于城市知识、研学设计和创作背景。Markdown 可以使用 Front Matter：

```yaml
---
title: 粤剧文化观察
city: 广州
category: 传统戏剧
source_name: 已核实的文化资料来源
source_url: https://www.ihchina.cn/
updated_at: 2026-10-20
---
```

示例地址用于展示字段格式，不代表该文档已经有项目级官方来源。实际编辑时请填写与正文事实对应的具体资料链接；无法核验则不要添加虚假的 `source_url`。

## 检索与使用边界

检索器结合 BM25、中文字符 n-gram、元数据加权与去重，并加入主题相关性阈值。匹配当前问题的官方记录获得优先权；未核实的辅助资料不能自动视为已验证事实。

场馆开放、演出场次、票价、预约及实时交通具有时效性，生成内容应提示用户以官方最新信息为准。更多实现细节见 [结构化知识库升级](KNOWLEDGE_BASE_UPGRADE.md) 与 [Agent V3](AGENT_V3.md)。

运行 `python -m scripts.run_benchmark` 验证当前检索回归。
