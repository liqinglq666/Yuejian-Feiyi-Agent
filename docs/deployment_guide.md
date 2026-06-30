# 粤见非遗部署指南

> 本文档说明如何在本地运行、上传 GitHub，并部署到 Streamlit Community Cloud。

---

## 1. 本地运行

### 1.1 进入项目目录

请确保终端所在目录与 `app.py` 同级。

```bash
cd Yuejian-Feiyi-Agent
```

项目结构应类似：

```text
Yuejian-Feiyi-Agent/
├── app.py
├── agent.py
├── rag.py
├── prompts.py
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── config.toml
├── data/
├── assets/
└── docs/
```

---

### 1.2 创建虚拟环境

Windows：

```bash
python -m venv venv
venv\Scripts\activate
```

macOS / Linux：

```bash
python -m venv venv
source venv/bin/activate
```

---

### 1.3 安装依赖

推荐使用清华源：

```bash
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### 1.4 配置 `.env`

复制 `.env.example` 为 `.env`。

Windows：

```bash
copy .env.example .env
```

macOS / Linux：

```bash
cp .env.example .env
```

然后编辑 `.env`：

```env
OPENAI_API_KEY=你的API_KEY
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus
```

---

### 1.5 启动项目

```bash
python -m streamlit run app.py
```

浏览器打开：

```text
http://localhost:8501
```

---

## 2. 阿里云百炼配置示例

```env
OPENAI_API_KEY=你的阿里云百炼 API Key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus
```

更低成本模型：

```env
OPENAI_API_KEY=你的阿里云百炼 API Key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-turbo
```

---

## 3. DeepSeek 配置示例

```env
OPENAI_API_KEY=你的 DeepSeek API Key
OPENAI_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
```

---

## 4. GitHub 上传注意事项

### 4.1 必须上传

```text
app.py
agent.py
rag.py
prompts.py
requirements.txt
README.md
.env.example
.gitignore
.streamlit/config.toml
data/
assets/
docs/
```

### 4.2 不能上传

```text
.env
.streamlit/secrets.toml
venv/
.venv/
__pycache__/
```

`.gitignore` 应包含：

```gitignore
.env
.streamlit/secrets.toml
__pycache__/
*.pyc
venv/
.venv/
.DS_Store
Thumbs.db
```

---

## 5. Streamlit Cloud 部署

### 5.1 基本流程

```mermaid
flowchart LR
    A[代码上传 GitHub] --> B[打开 Streamlit Community Cloud]
    B --> C[New app]
    C --> D[选择 GitHub 仓库]
    D --> E[Main file path 填 app.py]
    E --> F[配置 Secrets]
    F --> G[Deploy]
    G --> H[获得在线体验链接]
```

---

### 5.2 Main file path

填写：

```text
app.py
```

如果你的代码在子文件夹，比如：

```text
Yuejian-Feiyi-Agent/app.py
```

那就填：

```text
Yuejian-Feiyi-Agent/app.py
```

---

### 5.3 Secrets 配置

在 Streamlit Cloud 的 app 设置里，找到 **Secrets**，填写：

```toml
OPENAI_API_KEY = "你的API_KEY"
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen-plus"
```

注意：

- Secrets 使用 TOML 格式
- 等号两边建议留空格
- 字符串要加英文双引号
- 不要把真实 Key 写进 GitHub

---

## 6. 隐藏右上角 Deploy

项目中应存在：

```text
.streamlit/config.toml
```

内容：

```toml
[client]
toolbarMode = "viewer"

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#12b8b2"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f4faff"
textColor = "#101828"
```

修改后需要重新启动：

```bash
Ctrl + C
python -m streamlit run app.py
```

---

## 7. 常见问题

### 7.1 ModuleNotFoundError: No module named 'openai'

原因：依赖没有安装。

解决：

```bash
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### 7.2 未检测到模型 API Key

原因：

- `.env` 不在 `app.py` 同级目录
- `.env` 中变量名写错
- Streamlit Cloud 没配置 Secrets

检查 `.env`：

```env
OPENAI_API_KEY=xxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus
```

---

### 7.3 Streamlit Cloud 部署后报错

优先检查：

1. `requirements.txt` 是否存在
2. `app.py` 路径是否填写正确
3. Secrets 是否配置
4. API Key 是否有效
5. 模型名称是否可用
6. GitHub 是否上传了 `data/` 和 `assets/`

---

### 7.4 页面图片不显示

检查：

```text
assets/hero_feiyi.png
assets/qa_card.png
assets/route_card.png
assets/study_card.png
assets/content_card.png
```

这些文件是否存在。

如果图片不存在，应用仍可运行，但视觉效果会下降。

---

## 8. 部署前检查清单

| 检查项 | 是否完成 |
|---|---|
| 本地可以运行 `python -m streamlit run app.py` | ☐ |
| `.env` 已配置且未上传 GitHub | ☐ |
| `.env.example` 已上传 GitHub | ☐ |
| `.gitignore` 已包含 `.env` | ☐ |
| `requirements.txt` 已上传 | ☐ |
| `data/` 知识库已上传 | ☐ |
| `assets/` 图片资源已上传 | ☐ |
| `.streamlit/config.toml` 已上传 | ☐ |
| README 链接已更新 | ☐ |
| Streamlit Secrets 已配置 | ☐ |
| 在线体验链接可访问 | ☐ |
