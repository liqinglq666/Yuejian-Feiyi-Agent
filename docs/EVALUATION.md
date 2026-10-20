# 测试

后端使用 Pytest 和 Ruff；前端使用 TypeScript、ESLint 与 Playwright，GitHub Actions 会在 PR 及 `main` 推送时运行这些检查。

```bash
python -m pip install -r requirements-dev.txt
ruff check .
pytest
python -m scripts.run_benchmark

cd web
npm install
npm run typecheck
npm run lint
npm run build
npm run test:e2e
```

目前 `evaluation/benchmark.json` 含 60 条固定样例，检查场景路由、非遗主题检索和官方来源覆盖。Pytest 覆盖模型参数、网关安全、额度、检索、修订、导出、V3 场景规则和后端镜像一致性；Playwright 覆盖不同屏幕尺寸下的主要界面流程。

浏览器测试使用模拟模型响应。检索命中率、章节完整率和单元测试通过情况，不等于真实模型回答的事实准确率。真实生成质量和模型用量需要单独在受控额度下验证。
