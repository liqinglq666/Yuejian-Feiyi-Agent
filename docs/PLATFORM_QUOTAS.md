# 公开平台 API 额度控制

网站采用 Vercel Services（Next.js + FastAPI）。平台 AI 共享额度由 Upstash Redis 原子计数保护，**Redis 未配置或不可用时平台调用关闭**，个人自备 API 仍可使用。

在 Vercel 项目的 Storage/Marketplace 中安装 Upstash Redis，绑定 **yuejian-feiyi** 项目，确保 Production 环境具有以下**任意完整的一组**变量（可由集成自动注入，无需手动查看或复制密钥）：

- `UPSTASH_REDIS_REST_URL`
- `UPSTASH_REDIS_REST_TOKEN`（仅服务器端 Secret）

**Vercel Upstash Marketplace 常用另一套变量名称，网站现在同样支持：**

- `KV_REST_API_URL`
- `KV_REST_API_TOKEN`（仅服务器端 Secret）

后端优先使用完整的 `UPSTASH_REDIS_REST_*` 配对，找不到时使用完整的 `KV_REST_API_*` 配对，不会混用不同连接的 URL 和 Token。

已有的 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`MODEL_NAME` 仍保留。

可选限制，默认全站 60 次/UTC 天、同 IP 5 次/UTC 天、全站 8 次/分钟、同 IP 2 次/分钟：

- `PLATFORM_GLOBAL_DAILY_LIMIT=60`
- `PLATFORM_IP_DAILY_LIMIT=5`
- `PLATFORM_GLOBAL_MINUTE_LIMIT=8`
- `PLATFORM_IP_MINUTE_LIMIT=2`

请求使用 Upstash HTTP EVAL 执行原子 Lua 脚本，在生成或修改前同时检查四个计数器，检查与加一不可被并发绕过。一次请求计一次，与模型输出 token 数无关。产生失败也可能消耗名额，优先控制成本。计数为 UTC 自然日；分钟桶为 60 秒。错误时返回 429/503，网站提示访客改用个人 API。IP 来源在 Vercel 环境中使用 Vercel 覆写的 `x-vercel-forwarded-for`，其他环境使用 socket 地址；计数 key 为脱敏哈希，不储存明文 IP。

该计数限制**请求次数，不是精确货币预算或 token 上限**。还应在百炼服务商控制台设置消费预算与限额；生产商业运营应加入用户登录、验证码/Turnstile、分用户额度、审计及更强的 WAF 策略。不要把 Redis token 写入 `NEXT_PUBLIC_*`。

完成绑定后需要 Redeploy，验证 `/api/v1/status` 的 `platform_ready` 为 true，再完成一轮受控生成与修改测试。
