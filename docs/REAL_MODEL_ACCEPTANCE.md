# 粤见非遗 · 真实模型验收

历史上生产环境提供平台模型及 Redis 配置，而 PR Preview 没有独立测试凭据。实际环境设置可能变化，请在执行前以 Vercel 当前配置为准。不要将生产环境的模型 Key 复制到 Preview；不要通过聊天、提交或日志传递任何 Key。

## 运行前提

在模型供应商创建独立的低额度测试凭据，并在供应商后台设定消费上限。注意部分供应商预算提醒不是硬限额。在当前 `main` 或待验收的目标分支运行，并安装 `requirements-api.txt` 中的依赖。

PowerShell（仅设置当前终端会话变量，Read-Host 的密钥输入不会写入命令行历史）：

~~~powershell
$env:YUEJIAN_TEST_API_KEY = Read-Host "输入独立测试 Key"
$env:YUEJIAN_TEST_CONFIRM_SEPARATE_KEY = "YES"
$env:YUEJIAN_TEST_PROVIDER = "阿里云百炼"
$env:YUEJIAN_TEST_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:YUEJIAN_TEST_MODEL = "qwen3.7-flash"
python -m scripts.real_model_acceptance
Remove-Item Env:\YUEJIAN_TEST_API_KEY
~~~

按需调整模型名称或可信提供商，支持阿里云百炼、DeepSeek 和 OpenAI。不要将 Key 写入 .env、GitHub 代码、聊天或公用 Issue。

## 验收范围

该脚本直接调用当前分支的 FastAPI /v1/generate、/v1/revise 和 /v1/export，使用个人 BYOK 模式连接真实模型，不消耗生产环境共享额度。最多发生 **2 次模型调用**（生成、修改各一次），每次最多请求 **900 个输出 tokens**，关闭客户端自动重试和失败补全。具体费用仍取决于服务商实际的输入 token 和计费规则，测试前必须设定提供商侧预算上限。

验证流式事件、官方来源、回答结构、首字延迟、总耗时、修改及 Markdown 导出。日志仅打印数值和布尔状态，不打印 API Key 或生成正文。

脚本独立执行不代表本轮已经完成真实模型验证。真实生成后的事实内容应再由人工根据引用项目页面逐项核验，60 条 RAG 关键词评测不等于事实准确率。
