# 粤见非遗 · YUEJIAN

> 走近岭南，遇见非遗之美。一个面向广东文化探索、非遗研学、亲子体验与内容创作的全栈 AI 应用。

![粤见非遗岭南文化插画](./assets/readme_hero_lingnan.png)

## 全新 Web 架构

本仓库自 v2 起采用 **Next.js 16 + React 19 + TypeScript** 独立网页前端，并以 **FastAPI + Python** 作为服务端。原有非遗知识库、知识检索、提示词、修订规划、文档导出函数继续复用；Streamlit 仅保留为迁移前的兼容版本，不再作为新网站入口。

| 层级 | 技术 | 责任 |
| --- | --- | --- |
| Web | Next.js 16、React、TypeScript | 品牌首页、文化体验工作台、响应式设计与阅读交互 |
| Gateway | FastAPI、Pydantic | 输入校验、SSE 流式生成、导出、速率限制 |
| AI | 现有 `services/llm.py` | 平台模型与手动 BYOK；模型输出安全处理 |
| 知识 | 现有 `services/retrieval.py`、`data/` | 广东非遗知识库检索 |
| 业务 | `core/models.py`、`core/revisions.py` | 五场景条件、快捷修订与自定义修订 |
| 交付 | `services/export.py` | Markdown、TXT、Word 导出 |

## 本地启动

要求：Node.js 22+、Python 3.11+。

在仓库根目录分别启动服务：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-api.txt
cp .env.example .env
# 在 .env 中填写 OPENAI_API_KEY（或使用网页设置中的个人 API）
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

另开一个终端：

```bash
cd web
npm install
npm run dev
```

打开 **http://localhost:3000** 查看全新网站；前端通过 Next.js same-origin rewrite 转发 `/api/v1/*` 至 FastAPI `http://127.0.0.1:8000/v1/*`。

Windows 系统激活虚拟环境时使用 `.venv\\Scripts\\activate`，复制配置文件可使用 `copy .env.example .env`。

## API

- `GET /v1/status` — 服务状态、场景与可用修订预设（不包含密钥）
- `POST /v1/generate` — 接收结构化请求并返回 SSE `stage / snapshot / complete / failure`
- `POST /v1/revise` — 对当前方案进行快捷或自定义修订，维持原有后端校验规则
- `POST /v1/export` — 下载 `md / txt / docx`

新架构不会把个人 API Key 写入 localStorage、sessionStorage、Cookie、URL 或导出文件。个人 API 仅在当前页面状态保留，用户明确发起请求后才随 HTTPS POST 传给后端。服务端也不记录 API Key；生产请采用 HTTPS、密钥管理和额外的身份/限流防护。

## 项目结构

```text
web/
  app/page.tsx              # 岭南文化品牌首页
  app/studio/page.tsx       # AI 体验工作台
  app/globals.css           # 设计系统、响应式样式
  components/studio-app.tsx # 五场景、流式生成、修订、导出
  lib/api.ts                # API 与 SSE 客户端
  lib/types.ts              # TypeScript 业务模型
  public/heritage-hero.png  # 复用仓库原有岭南插画
api/main.py                 # FastAPI 独立服务端
core/                       # 原有 Python 领域模型与修订逻辑
services/                   # 原有模型、知识检索、导出服务
data/                       # 广东非遗知识库
app.py                      # 旧版 Streamlit（兼容参考）
```

## 部署建议

- 前端：Vercel 或任意支持 Next.js 的 Node.js 运行环境。在前端环境变量中配置 `API_INTERNAL_URL=https://your-api.example.com`。
- 后端：Render、Railway 或自建容器，启动 `uvicorn api.main:app --host 0.0.0.0 --port 8000`。
- 后端环境变量：`OPENAI_API_KEY`、`OPENAI_BASE_URL`（可选）、`MODEL_NAME`（可选）、`WEB_ALLOWED_ORIGINS` 与 `GENERATE_RATE_LIMIT_PER_MIN`。
- 匿名演示环境必须在 API 网关配置共享限流与用量上限；如正式公开服务，建议增加登录、配额、请求审计和 Redis 限流。
- 前端和后端为独立进程，**不能直接把仓库作为 Streamlit Cloud 项目部署成新 Web 版**。

> 现有 Streamlit 演示站点： https://yuejian-feiyi-agent.streamlit.app/ （仅用于旧版参考，不代表 Next.js 新站已部署）。

## 测试

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
cd web
npm install
npm run typecheck
npm run lint
npm run build
```

更多技术与迁移说明见 [docs/WEB_ARCHITECTURE.md](docs/WEB_ARCHITECTURE.md)。

**版权与文化内容声明：** 文化资料用于体验设计与信息参考；景点开放、票务、预约、演出与交通等动态数据请以官方平台最新公告为准。
