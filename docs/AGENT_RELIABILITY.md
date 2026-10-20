# 非遗 Agent：可靠性与 AI 服务配置

## 可信知识与来源
首批 8 个官方项目条目存放于 `data/heritage_records.json`，包含城市、类别、项目编号、来源和核验日期。未完成官方核验的旧文档继续用于写作建议，但不能作为项目级别或开放时间的证据。来源页不等于实时场馆信息。

## 流式接口
`/v1/generate` 和 `/v1/revise` 保持 SSE 接口：
- `stage`：检索与生成状态
- `snapshot`：初始化文本或清洗导致的全量重写
- `delta`：自上一份文本后新增的内容，降低持续传输开销
- `complete`：完整结果、来源、请求、`metrics`、`quality`
- `failure`：人类可读的失败原因

`metrics.first_token_ms` 仅统计进入模型生成阶段后的首字延迟，`total_ms` 同样不含检索准备时间；它们不是整个网页端到端耗时。传输限频为 120ms 左右。若模型连接在传输中断后仍继续计费，不能保证可获得供应商额度返还。

`quality` 仅检查标题完整性与官方来源数量，**不代表事实准确或答案可被官方认证**。

## 模型连接与额度
- 平台 AI 继续使用现有 Upstash 原子限额；当 Redis 配置缺失或不可用时平台请求失败关闭。
- 生产环境个人 BYOK 仅默认允许 `dashscope.aliyuncs.com`、`api.deepseek.com` 与 `api.openai.com`。
- 如需其他 OpenAI-compatible 供应商，先核对其可信 HTTPS API 域名，再在 Vercel 服务端配置 `BYOK_ALLOWED_HOSTS`（以英文逗号分隔的**准确主机名**），重新部署。不要将此变量或 API Key 设为 `NEXT_PUBLIC_*`。自定义域名 DNS 检查不能等同完整的网络层出站隔离；长期建议使用服务端出站代理或固定网关。
- 导出接口设置单实例频率限制，它不承担全局付费限额；公开站点仍建议加 WAF/Turnstile。
- 平台请求数限额不是精确 Token 预算，应在模型供应商控制台设置实际消费上限。

## 回归测试
`python -m scripts.run_benchmark`：40 条路由、检索与官方来源覆盖用例。
`pytest`：知识库验证、错误来源拒绝、模型连接、导出和输出检查。
`cd web && npm run test:e2e`：375px、768px、1440px 前端流程（使用模拟的模型响应）。
合并生产前应在受控额度下额外验证**一次真实生成、一次修改、一次失败/取消情形**；不要拿模拟接口回归冒充真实模型压测。
