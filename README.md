# 粤见非遗

广东非遗导览与内容整理工具。用户提供城市、时间、出行对象和兴趣后，系统结合本地知识库生成路线建议、文化讲解、研学任务和传播文案。

在线地址：<https://yuejian-feiyi-agent.streamlit.app/>

## 功能

- 广东非遗知识问答
- 半日、一日及周末路线建议
- 亲子和学生研学任务
- 小红书、公众号等图文文案
- 短视频分镜与旁白
- 基于上一版结果继续调整
- Markdown、TXT 和 Word 导出

开放时间、票价、交通、预约和活动安排属于实时信息，生成结果会提示用户以官方渠道为准。

## 工作流程

```mermaid
flowchart LR
    A[用户需求] --> B[任务类型识别]
    B --> C[本地知识库检索]
    C --> D[Prompt 组装]
    D --> E[OpenAI-compatible 模型]
    E --> F[结果展示与导出]
```

任务类型通过关键词分为：

```text
qa
route
study
social
video
```

知识库检索失败时程序会明确报错，不会把故障当作“没有相关资料”。

## 本地运行

```bash
python -m venv .venv
```

Windows：

```bash
.venv\Scripts\activate
```

macOS / Linux：

```bash
source .venv/bin/activate
```

安装并启动：

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## 模型配置

页面左侧需要填写：

```text
API Key
Base URL
Model
```

默认示例：

```text
Base URL  https://dashscope.aliyuncs.com/compatible-mode/v1
Model     qwen-turbo
```

Base URL 默认要求 HTTPS，并拒绝回环、内网和保留地址。部署方还可以通过 `LLM_ALLOWED_HOSTS` 限制允许访问的模型网关。

本地调试确实需要 HTTP 时，可以显式设置：

```text
ALLOW_INSECURE_LLM_HTTP=true
```

不要在公开部署或仓库中保存真实 API Key。

## 知识库

RAG 读取项目内的广东非遗资料。新增资料时：

- 使用 UTF-8 文本格式；
- 保留明确的项目名、城市和类别；
- 不要把未经核验的票价、开放时间等实时信息写成固定事实；
- 修改后先检查检索结果，再调整 Prompt。

## 目录

```text
.
├── app.py              # Streamlit 界面
├── agent.py            # 模型调用和任务识别
├── rag.py              # 本地知识库检索
├── prompts.py          # 系统和任务 Prompt
├── knowledge/          # 非遗资料
├── assets/             # 页面图片
├── tests/
└── requirements.txt
```

## 测试

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

## 数据与隐私

- API Key 只用于模型请求，不应写入源码。
- 用户输入可能包含行程和身份信息，公开部署时应说明数据处理方式。
- 模型生成内容需要人工核验，尤其是实时信息和文化事实。

## License

见仓库中的许可文件。
