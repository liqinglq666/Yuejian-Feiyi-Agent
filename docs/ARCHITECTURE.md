# 架构说明

## 设计目标

粤见非遗将 UI、状态、检索、Prompt 和模型调用分层，保证主流程清晰、可测试、可替换。

## 请求生命周期

1. `ui/workspace.py` 收集用户输入与结构化条件。
2. `TaskRequest` 保存场景、城市、时间、身份、兴趣和原始需求。
3. `TaskRequest.task_type` 由场景显式映射，不依赖拼装后的长 Prompt 猜测任务类型。
4. 首次生成使用知识相关字段构造 retrieval query。
5. `services/retrieval.py` 通过 BM25、中文字符 n-gram、元数据加权、去重与字符预算返回 `RetrievalBundle`。
6. `services/prompt_builder.py` 将结构化条件、检索上下文和任务规则组装为模型消息。
7. `core/config.py` 根据 `auto / platform / user` 三种模式解析模型配置，并保证自动模式不会静默消耗用户自己的额度。
8. 平台共享配置来自服务端环境变量或 Streamlit Secrets；用户 BYOK 配置只来自当前 `st.session_state`。
9. `services/llm.py` 负责模型网关校验、调用、超时、错误映射与安全流式回退。
10. `services/output.py` 对最终文本进行展示前清洗，包含移除 RAG 内部来源编号等技术标记。
11. `core/state.py` 保存当前方案、最近方案和调整历史；个人 API Key 只保存在当前 Session State，且不会进入方案数据。
12. `ui/results.py` 按任务类型展示结果，并提供 Markdown、TXT、Word 导出。

## 模型配置与路由边界

### 平台 API

平台 API Key、Base URL 和模型名称只由部署者设置。`PLATFORM_API_ENABLED=false` 可以主动关闭平台服务，而无需删除 Key 或修改代码。

平台模型地址可以通过 `LLM_ALLOWED_HOSTS` 锁定到预期域名。公网部署仍应在托管平台、反向代理或 API 网关层增加限流、访问控制与预算保护。

### 用户 BYOK

用户可以明确切换到“我的 API”，并在当前 Streamlit 会话中填写 API Key、Base URL 与模型名称。

个人 API Key：

- 只保存在当前 `st.session_state`
- 不写入最近方案、导出文件、数据库、URL 或日志
- 不提供跨会话持久恢复
- 可通过“清除我的 API Key”立即删除

用户自定义 Base URL 不受平台 `LLM_ALLOWED_HOSTS` 限制，否则无法使用不同服务商；但仍必须使用安全模型网关规则：默认 HTTPS，禁止 localhost、内网、link-local、multicast、reserved、unspecified 地址，以及 URL 中的账号密码、query 和 fragment。

### 自动模式

`auto` 模式只在平台 API 可用时使用平台额度。如果平台未配置、被关闭或运行时调用失败，应用只提示用户切换到个人 API，不会自动使用已保存的个人 Key。这是为了避免未经确认消耗用户自己的额度。

## 连续调整

状态围绕以下三部分组织：

- `root_request`
- `current_answer`
- `revision_history`

继续调整时，系统使用当前生效条件、当前答案和本轮修改要求重新生成；检索查询可补充本轮修改要求中的知识相关信息，但不会递归复用上一轮完整 Prompt。

## RAG 展示边界

RAG 检索仍参与生成，但面向用户的正文不展示 `[S1]`、`[S2]` 等内部来源编号。知识来源信息仅作为辅助核验信息使用；实时开放、票务、预约、演出和交通信息仍要求用户以官方平台最新公告为准。

## 兼容层

根目录的 `agent.py`、`rag.py` 和 `prompts.py` 保留旧版公共导入入口。Streamlit Web 主流程直接使用 `core/`、`services/` 与 `ui/`，不依赖兼容层完成主要交互。
