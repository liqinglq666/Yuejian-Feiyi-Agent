# 粤见非遗 · YUEJIAN

广东非遗文化体验 AI 助手，支持路线规划、学生研学、亲子体验、内容创作和非遗问答。

**在线体验：** https://yuejian-feiyi.vercel.app/

![岭南文化插画](./web/public/heritage/lingnan-festival-hero-desktop.webp)

## 功能

- 五种文化探索任务，支持自然语言提出需求
- 广东非遗知识检索：12 条结构化官方项目记录与场景资料
- 项目来源可追溯；动态演出、票价、场馆开放信息会提示核验
- 流式生成、快捷修改、自定义调整
- Markdown、TXT 和 Word 导出
- 平台 AI 每日额度保护，或选择使用个人 API

检索到官方来源不等于 AI 生成内容的所有事实均已获得核实；重要行程信息请以官方公布为准。

## 代码结构

| 位置 | 作用 |
| --- | --- |
| `web/` | Next.js 16、React 19 与响应式前端 |
| `api/`、`core/`、`services/` | FastAPI 接口、任务处理、RAG、模型调用及导出 |
| `data/` | 非遗资料与来源记录 |
| `backend/` | Vercel Backend Service 的独立部署镜像 |
| `evaluation/`、`tests/`、`web/tests/` | 60 条检索评测、Python 和浏览器回归测试 |
| `services/scenarios.py` | V3 的场景专属策略与结果自检 |

`backend/` 镜像目前服务于 Vercel 多服务部署，修改根目录的 Python 核心逻辑时需同步相应后端文件。

## 本地运行

要求：Node.js 22+、Python 3.11+。

终端一：

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-api.txt
cp .env.example .env
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
~~~

终端二：

~~~bash
cd web
npm install
npm run dev
~~~

打开 http://localhost:3000 。可在网页 AI 设置中配置自己的 API；平台 AI 需要正确配置模型密钥及 Redis 配额服务。

## 测试

~~~bash
pip install -r requirements-dev.txt
ruff check .
pytest
python -m scripts.run_benchmark
cd web
npm run typecheck
npm run lint
npm run build
npm run test:e2e
~~~

技术细节见 `docs/ARCHITECTURE.md`、`docs/AGENT_RELIABILITY.md` 和 `docs/KNOWLEDGE_BASE_UPGRADE.md`。

**提示：** 非遗现场体验、营业信息与活动日程以举办单位和官方平台最新公告为准。
