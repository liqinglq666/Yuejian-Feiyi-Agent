# 系统架构

网站由 Next.js 前端和 FastAPI 后端组成。生产环境使用 Vercel Services：`web/` 构建前端，`backend/` 构建 Python API。`vercel.json` 将 `/api/v1/*` 转到后端，其他页面请求交给前端。

根目录的 `api/`、`core/`、`services/`、`data/` 用于本地开发和测试；`backend/` 是上线所需的完整镜像。修改这些模块时须同时修改镜像，相关测试会检查文件一致性。

## 任务处理

1. 前端根据用户选择构造 `TaskRequest`，包括城市、时长、兴趣和场景。
2. `api/main.py` 验证参数和请求频率。平台调用通过 Upstash Redis 预留共享额度；个人 BYOK 使用单独的地址校验和模型配置。
3. `services/scenarios.py` 按场景应用规则：游客路线、研学、亲子、问答，以及内容创作的图文与短视频模式。`services/planner.py` 生成确定性的任务步骤。
4. `services/retrieval.py` 从本地非遗资料中检索候选片段，`services/prompt_builder.py` 组织本次生成或修改的模型消息。
5. `services/llm.py` 访问模型服务，`services/output.py` 清理文本，`services/quality.py` 检查预定章节和来源主题匹配。
6. 后端通过 SSE 把结果发给前端，前端支持阅读、继续修改，以及 Markdown、TXT 和 DOCX 导出。

快捷与自定义修改先由 `core/revisions.py` 更新生效的任务条件，再走同一条生成链路。场景规划和结构检查不额外调用模型。

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/v1/status` | 服务状态与可用场景 |
| POST | `/v1/generate` | 流式生成 |
| POST | `/v1/revise` | 修改已有方案 |
| POST | `/v1/export` | 下载 md / txt / docx |

正式网站使用同源 `/api/v1/*` 路径；在本地 Next.js 通过 `web/next.config.ts` 转发到 `127.0.0.1:8000`。

流式接口按需要发送 `stage`（状态）、`snapshot`（完整文本快照）、`delta`（新内容）、`complete`（最终结果）、`failure`（错误）。完成事件带有来源、章节检查结果及生成阶段的首字/总耗时。这两个耗时不包括检索准备和前端传输，不能当作页面端到端延迟。

## 资料与校验

`data/heritage_records.json` 为结构化项目记录，`data/*.md` 为城市路线、研学与创作资料。检索采用 BM25、中文字符 n-gram、元数据加权和片段去重，返回数量及总长度均有限制。

`quality.official_source_count` 统计与用户主题直接匹配的官方项目记录，并不能证明答案中的每句话都获得相应来源支持。场景安全提示也是关键词/规则层面的提醒，不涉及现场条件的实际核查。路线目前未接入地图、开放时间及票务系统。

## 模型访问

平台共享调用由 Upstash Redis 的原子限额保护；Redis 不可用时拒绝平台付费请求。个人 BYOK 不使用共享额度，密钥只在当前页面内存中保留，并通过 HTTPS 请求发送至后端。生产 BYOK 允许的 API 主机受服务端列表控制；默认包括百炼、DeepSeek 和 OpenAI，扩展供应商需核对并配置 `BYOK_ALLOWED_HOSTS`。

生成及导出接口的部分频率限制按服务实例计算，不能代替全局网关防护和模型服务商的费用上限。中途取消不保证已经产生的费用会被退回。

相关说明：[Vercel 部署](VERCEL_DEPLOYMENT.md)、[平台额度](PLATFORM_QUOTAS.md)、[知识库](KNOWLEDGE_BASE.md)、[评测](EVALUATION.md)。
