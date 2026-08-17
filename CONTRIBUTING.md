# Contributing

感谢参与粤见非遗。

## 开发流程

1. 从 `main` 创建功能分支。
2. 安装 `requirements-dev.txt`。
3. 修改代码时补充或更新测试。
4. 提交前运行：

```bash
ruff check .
python -m compileall -q .
pytest
```

5. Pull Request 说明问题、方案、测试结果和界面变化。

## 知识库贡献

新增知识资料时必须标注来源名称和链接，不提交真实 API Key、个人隐私信息或大段受版权保护内容。
