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
7. `core/config.py` 只从服务端环境变量读取 API Key、Base URL 和模型名称，不接受网页用户提供的模型配置。
8. `services/llm.py` 负责模型网关校验、调用、超时、错误映射与安全流式回退。
9. `services/output.py` 对最终文本进行展示前清洗，包含移除 RAG 内部来源编号等技术标记。
10. `core/state.py` 保存当前方案、最近方案和调整历史，不保存模型密钥或用户自定义模型网关。
11. `ui/results.py` 按任务类型展示结果，并提供 Markdown、TXT、Word 导出。

## 服务端模型配置边界

Web 用户只提交非遗任务内容和结构化偏好。模型 API Key、Base URL 与模型名称属于部署配置，不进入 Session State，也不通过输入框暴露给用户。

生产环境应优先设置 `LLM_ALLOWED_HOSTS` 锁定模型服务域名，并在托管平台、反向代理或 API 网关层增加限流与预算控制。

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
