# 粤见非遗 · 当前架构

正式服务采用 **Next.js + React 前端**、**FastAPI + Python 后端**，由 Vercel 多服务项目部署，不再依赖 Streamlit。

## 请求生命周期

1. `web/app/page.tsx` 和 `web/components/studio-app.tsx` 收集五种任务场景与结构化条件。
2. `api/main.py` 使用 Pydantic 验证参数，解析平台或用户 BYOK 模型，并在预留平台额度前检查场景与任务类型一致性。
3. `services/scenarios.py` 定义游客路线、研学、亲子、图文、视频和问答的独立策略；图文与视频属于内容创作的两个子模式。
4. `services/retrieval.py` 检索 `data/` 下的广东非遗知识与结构化官方项目来源。
5. `services/planner.py` 及 `services/prompt_builder.py` 按场景规划任务并构建生成提示，不增加额外付费模型调用。
6. `services/llm.py` 完成模型调用与流式传输；`services/output.py` 清洗输出；`services/quality.py` 做章节、来源和场景的启发式检查。这些检查不等于事实逐条认证。
7. 前端支持继续调整、结果阅读和 Markdown/TXT/Word 导出。修改规则位于 `core/revisions.py`，导出位于 `services/export.py`。

## 部署结构

`vercel.json` 声明 frontend (`web/`) 与 backend (`backend/`) 两个服务。根目录 `api/`、`core/`、`services/`、`data/` 用于本地开发和测试；`backend/` 保存服务部署所必需的独立代码镜像，不能随意删除。后端功能修改需要同步镜像，CI 会测试一致性。

## 服务和安全

平台共享模型使用 Upstash Redis 的共享额度限制，网络访问还应由服务商预算和可信出站规则约束。用户 BYOK API Key 保存在网页当前运行态，不写入浏览器持久化存储、Git 或导出文件。

官方非遗项目条目用于文化知识核验，不保证实际演出、场馆开放、票价、活动、预约与交通数据的实时准确性。

## 测试

执行 `pytest`、`python -m scripts.run_benchmark`，以及在 `web/` 内执行 `npm run typecheck`、`npm run lint`、`npm run build` 和 `npm run test:e2e`。浏览器测试使用模拟生成事件，不代表真实付费模型的验收结果。
