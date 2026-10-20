# Next.js / FastAPI Web

## 页面与 API

生产网站由 Next.js 前端和 FastAPI API 组成，采用 Vercel 多服务路由。现有首页包含五种文化任务入口、输入表单与岭南主题插画；工作台支持条件编辑、SSE 流式生成、修改、阅读与导出。

前端主要文件：`web/app/page.tsx`、`web/components/studio-app.tsx`、`web/lib/api.ts`。页面样式由 `web/app/globals.css` 和 `web/app/folk-art.css` 提供。素材位于 `web/public/heritage/`。

同源 API：
- `GET /api/v1/status`
- `POST /api/v1/generate`（stage、snapshot、delta、complete、failure）
- `POST /api/v1/revise`
- `POST /api/v1/export`（Markdown、TXT、DOCX）

## V3 业务

后端从 `services/scenarios.py` 获取场景策略；初次生成和后续修改共用策略规则，但按任务提供不同的规划、保守处理要求和启发式结果提示。输入缺少城市、儿童年龄或学段时不会擅自猜测。

## 部署与约束

`vercel.json` 将 `web/` 作为前端服务、`backend/` 作为 FastAPI 服务。根目录代码用于开发；后端镜像必须保持同步。

实时场馆信息、交通时间、票务和开放时段没有可靠来源时应以核验建议代替确定性结论。平台 AI 的额度保护和用户 BYOK 域名安全策略仍在 FastAPI 中实现。真实模型性能需额外进行受控验证。
