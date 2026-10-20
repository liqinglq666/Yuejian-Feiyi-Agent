# Security Policy

请不要在公开 Issue 共享 API Key、可利用漏洞或私人数据。请通过仓库维护者的私人联系方式报告安全问题。

## 凭据和隐私

- 平台模型密钥只能部署在服务端环境变量中，不能放在 `NEXT_PUBLIC_*`、前端 bundle、Git、日志、导出文件或公开截图。
- 个人 BYOK Key 只保留在当前网页内存状态；由用户明确发起 HTTPS 请求时传入 FastAPI，不写入 localStorage、sessionStorage、Cookie、URL 或持久数据库。
- 不要提交 `.env` 或其他秘密文件。泄漏后应在服务商处立即撤销并更换密钥；删除当前 Git 文件不会自动消除 Git 历史中的泄漏。

## 模型与网络

- 平台 AI 使用 `PLATFORM_API_ENABLED` 控制开关，使用 `LLM_ALLOWED_HOSTS` 约束服务商主机。
- 生产 BYOK 使用默认可信 API 域名；额外域名须通过服务端 `BYOK_ALLOWED_HOSTS` 显式允许。
- API 地址强制安全格式校验；网络层仍建议采用可信出站代理隔离，防止 SSRF。
- 自动模式不会在平台不可用时改用用户的 Key 消耗个人额度。

## 风险和成本

平台共享调用受 Upstash Redis 额度约束；单实例速率限制不是分布式安全防护。公开站点仍应设置 WAF、合理预算、模型调用审计与异常告警。取消生成不保证已计费用能被退款。
