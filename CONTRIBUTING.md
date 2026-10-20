# 参与贡献

从 `main` 建立分支，提交 PR 时说明改了什么、为什么修改以及测试结果。

- Python：运行 `ruff check .`、`pytest`、`python -m scripts.run_benchmark`。
- 前端：在 `web/` 执行 `npm run typecheck`、`npm run lint`、`npm run build`，涉及交互时运行 `npm run test:e2e`。
- 修改 `api/`、`core/`、`services/` 或 `data/` 时，同时更新 `backend/` 对应的部署镜像。
- 知识库补充资料请保留可核对的来源，不要上传密钥、个人隐私或大段受版权保护的材料。
