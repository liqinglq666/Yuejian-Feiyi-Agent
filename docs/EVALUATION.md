# 测试与评测

本项目的正式运行架构为 **Next.js + FastAPI + V3 场景 Agent**。自动化检查覆盖代码正确性、页面交互和检索可追溯性，但不将模型生成质量和事实准确率等同于自动测试分数。

## 1. 自动化测试

`pytest` 在 Python 3.11 和 3.14 下覆盖：

- `TaskRequest`、五种公开场景与六种内部策略（图文/视频为两个子模式）
- 场景规划、快捷与自定义修改、条件一致性及结果结构诊断
- 结构化官方名录、混合检索、来源有效性和主题相关性
- FastAPI `/v1/status /v1/generate /v1/revise /v1/export`
- 模型路由、BYOK 地址校验、Redis 限额、SSE 处理及导出
- Vercel `backend/` 与根目录核心服务代码的一致性

前端使用 Next.js 16、TypeScript、ESLint 和 Playwright Chromium，检查 375 / 768 / 1440px 的主要交互流程。浏览器测试的模型响应是**模拟数据**。

## 2. RAG Benchmark

样例文件：`evaluation/benchmark.json`（当前 **60 条**，覆盖五种业务场景和 12 个结构化非遗项目）。

执行：

```bash
python -m scripts.run_benchmark
```

脚本分别统计 **任务类型路由、检索主题命中、官方项目来源覆盖**。这些分数不能解释为生成答案的真实性、可执行率或客观准确率，也不能据此宣称检索已覆盖全部广东非遗项目。

## 3. 本地复现

```bash
python -m pip install -r requirements-dev.txt
ruff check .
python -m compileall -q .
pytest
python -m scripts.run_benchmark

cd web
npm install
npm run typecheck
npm run lint
npm run build
npm run test:e2e
```

CI 配置见 `.github/workflows/ci.yml`。

## 4. 尚未自动验证的部分

真实模型生成、修改与费用受第三方模型供应商影响，需在受控预算下独立验收；现有的 `scripts/real_model_acceptance.py` 可供测试。推荐补充人工逐条事实核对、场景可执行性评分、首字/总时延以及模型 Token 消耗统计。未经同版本复现，不对外宣称具体生成准确率。
