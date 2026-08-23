# 评测说明

## 当前评测层级

### 单元测试

覆盖任务路由、状态管理、检索、Prompt、安全校验、输出清洗和主要 UI 辅助逻辑。

### 基础 Benchmark

`evaluation/benchmark.json` 用于检查：

- 场景是否映射到正确任务类型
- 检索结果是否包含预期城市或非遗项目

运行：

```bash
python scripts/run_benchmark.py
```

## 推荐扩展指标

- Task routing accuracy
- Recall@K / MRR
- 检索相关性
- 事实错误率
- 输出结构完整率
- 首字延迟与总响应时间
- 平均 Token 消耗

面向用户的结果不显示 RAG 内部来源编号，因此不再把“来源编号覆盖率”作为产品展示指标。任何对外展示的百分比都应来自固定数据集、固定版本和可复现脚本。
