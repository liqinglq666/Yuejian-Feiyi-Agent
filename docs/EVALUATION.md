# 评测说明

## 当前评测层级

### 单元测试

覆盖任务路由、状态管理、检索、Prompt、安全校验和输出清洗。

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
- 来源标注覆盖率
- 事实错误率
- 输出结构完整率
- 首字延迟与总响应时间
- 平均 Token 消耗

任何对外展示的百分比都应来自固定数据集、固定版本和可复现脚本。
