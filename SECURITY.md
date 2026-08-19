# Security Policy

## 报告安全问题

请不要通过公开 Issue 披露 API Key、可利用漏洞或用户隐私数据。请通过仓库所有者公开的安全联系方式进行私下报告。

报告应包含：

- 受影响文件或功能
- 复现步骤
- 风险影响
- 建议修复方式

## 密钥安全

应用同时支持平台共享 API 与用户 BYOK，两类密钥必须严格隔离：

- 平台 API Key、Base URL 和模型名称只由项目维护者在服务端部署环境或 Streamlit Secrets 中配置
- 平台密钥不得写入 `st.session_state`、前端 HTML、日志、URL、下载文件或公开仓库
- 用户 BYOK 的 API Key 仅允许保存在当前 Streamlit Session State 中
- 用户 Key 不得写入最近方案、数据库、浏览器持久化存储、导出文件、URL、日志或异常信息
- “清除我的 API Key”必须立即清空当前会话中的个人 Key；关闭会话后不提供持久恢复
- 不要提交 `.env` 或 `.streamlit/secrets.toml`
- 发现密钥泄露后应立即在服务商控制台撤销并重新生成
- Git 历史中的密钥需要通过历史清理工具移除，单纯删除当前文件不够

## 模型路由

- `自动`模式只会使用平台 API，不会在平台失效时静默切换并消耗用户自己的额度
- 使用个人 API 必须由用户明确切换到“我的 API”
- 平台共享服务可通过 `PLATFORM_API_ENABLED=false` 主动关闭，而不影响用户继续使用 BYOK
- 测试个人 API 连接会产生一次很小的真实模型调用，应仅在用户主动点击时执行

## 模型网关

应用默认拒绝 HTTP、本机、内网、link-local、multicast、reserved 和 unspecified 地址，并拒绝 URL 中的账号密码、query 与 fragment。只有完全可信的本地开发环境才应设置 `ALLOW_INSECURE_LLM_HTTP=true`。

生产环境建议设置 `LLM_ALLOWED_HOSTS`，只允许平台共享 API 访问预期模型服务域名。该平台白名单不用于限制用户选择不同的公网 OpenAI-compatible 服务，但用户 BYOK 仍必须通过 HTTPS 与地址安全检查。

公网部署使用平台共享 API 时，还应在托管平台、反向代理或 API 网关增加访问控制、限流、预算告警和异常调用监控，避免匿名滥用消耗额度。
