# 架构说明

## 设计目标

重构后的核心目标是把 UI、状态、检索、Prompt 和模型调用分开，并保证每个模块可单独测试。

## 请求生命周期

1. `ui/workspace.py` 收集用户输入。
2. `TaskRequest` 将场景、城市、时间、身份和兴趣结构化。
3. `TaskRequest.task_type` 由场景显式映射，不从长 Prompt 猜测。
4. `TaskRequest.retrieval_query` 只包含知识相关字段。
5. `services/retrieval.py` 返回带来源元数据的 `RetrievalBundle`。
6. `services/prompt_builder.py` 生成一次且唯一的任务 Prompt。
7. `services/llm.py` 调用兼容模型接口并处理安全与错误。
8. `core/state.py` 保存最初请求、当前答案和简短修改历史。

## 连续优化模型

状态只保存：

- `root_request`
- `current_answer`
- `revision_history`

每轮修改不会保存或复用上一轮完整 Prompt。这样可以控制 Token 增长，并确保检索查询始终围绕最初需求。

## 兼容层

根目录的 `agent.py`、`rag.py` 和 `prompts.py` 保留旧版导入入口，但 Web 应用不依赖旧版关键词路由。
