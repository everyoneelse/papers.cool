# arXiv Advanced Search 和数据对比工具

## 🎯 项目概述

这个工具集帮助你验证本地 arXiv 论文数据与官方搜索结果的一致性，确保数据完整性和准确性。

### 核心功能

✅ **arXiv 官方 Advanced Search**  
- 支持关键词搜索（标题、摘要、作者）
- 支持分类过滤
- 支持日期范围查询
- 自动处理分页和速率限制

✅ **数据完整性对比**  
- 对比本地数据与 arXiv 官方结果
- 识别缺失或额外的论文
- 生成详细的对比报告（JSON + Markdown）
- 计算匹配率和统计信息

✅ **易用性**  
- 命令行工具（开箱即用）
- Python API（可集成到现有代码）
- 完善的文档和示例

## 📦 文件结构

```
examples/
├── README.md                           # 本文件
├── QUICKSTART.md                       # 快速开始指南
├── SUMMARY.md                          # 功能总结
├── README_comparison.md                # 详细对比工具文档
├── compare_local_with_arxiv.py         # 主对比工具
├── quick_test.py                       # 快速测试脚本
├── integrate_with_search_engine.py     # 集成示例
└── test_output/                        # 测试输出目录

src/scripts/
└── arxiv_advanced_search.py            # 核心实现
```

## 🚀 快速开始

### 1. 测试 API 连接

```bash
cd /home/hy/project/papers.cool/arxiv-paper-curator
python examples/quick_test.py
```

### 2. 对比本地数据

```bash
# 对比指定日期的所有分类
python examples/compare_local_with_arxiv.py --date 2024-11-25

# 对比特定分类
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --categories cs.AI cs.CV

# 搜索特定关键词
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --keywords "large language model"

# 保存详细报告
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --output ./comparison_results
```

## 📚 文档导航

### 新手入门
- 📖 [快速开始指南](./QUICKSTART.md) - 3 分钟上手
- 🎓 [功能总结](./SUMMARY.md) - 完整功能说明

### 深入使用
- 📘 [对比工具详细文档](./README_comparison.md) - 所有参数和选项
- 💻 [集成示例](./integrate_with_search_engine.py) - 如何集成到现有代码

## 🔍 核心功能详解

### 1. arXiv Advanced Search

使用 arXiv 官方 API 进行高级搜索：

```python
from src.scripts.arxiv_advanced_search import ArxivAdvancedSearch
from datetime import datetime

searcher = ArxivAdvancedSearch()

# 搜索指定日期和关键词的论文
results = searcher.search(
    keywords="large language model",
    categories=["cs.AI", "cs.CL"],
    date_from=datetime(2024, 11, 25),
    date_to=datetime(2024, 11, 25),
    max_results=1000
)

print(f"Found {len(results)} papers")
for paper in results:
    print(f"{paper['arxiv_id']}: {paper['title']}")
```

### 2. 数据完整性对比

对比本地数据与 arXiv 官方结果：

```bash
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --output ./comparison_results
```

输出示例：

```
================================================================================
arXiv Data Comparison Report - 2024-11-25
================================================================================

📊 Overall Statistics:
  arXiv Official: 156 papers
  Local Data:     156 papers
  Matched:        156 papers
  Match Rate:     100.00%

📋 By Category:
  cs.AI:
    arXiv: 23, Local: 23, Matched: 23 (100.0%)
  
  cs.CV:
    arXiv: 45, Local: 44, Matched: 44 (97.8%)
    ⚠️  Missing in local (1):
       - 2411.12345
```

### 3. 集成到现有代码

参考 [integrate_with_search_engine.py](./integrate_with_search_engine.py) 了解如何：
- 集成到你的 `search_engine.py`
- 在 Streamlit UI 中添加验证功能
- 实现自动化数据质量检查

## 📊 使用场景

### 场景 1: 每日数据验证

```bash
#!/bin/bash
# daily_validation.sh

YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

# 运行对比
python examples/compare_local_with_arxiv.py \
    --date $YESTERDAY \
    --output ./validation_reports/$YESTERDAY

# 检查结果
MATCH_RATE=$(cat ./validation_reports/$YESTERDAY/comparison_report_*.json | \
    jq '.summary.overall_match_rate')

if (( $(echo "$MATCH_RATE < 95" | bc -l) )); then
    echo "⚠️  Warning: Match rate is ${MATCH_RATE}%"
    # 发送告警邮件
fi
```

### 场景 2: 批量验证

```bash
# 验证过去一周的数据
for i in {1..7}; do
    DATE=$(date -d "$i days ago" +%Y-%m-%d)
    python examples/compare_local_with_arxiv.py \
        --date $DATE \
        --output ./weekly_validation/$DATE
done
```

### 场景 3: 特定主题覆盖率

```bash
# 检查 LLM 相关论文的覆盖情况
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --keywords "large language model" \
    --categories cs.AI cs.CL cs.LG \
    --output ./llm_coverage
```

## 🛠️ 技术细节

### arXiv API 特性

- **搜索语法**: 支持 `ti:`, `abs:`, `au:`, `cat:` 等字段
- **组合查询**: 支持 `AND`, `OR`, `()` 逻辑运算
- **速率限制**: 自动遵守 3 秒/请求的限制
- **分页处理**: 自动处理超过 1000 条的结果

### 对比逻辑

1. **ID 规范化**: 移除版本号（`2411.12345v1` → `2411.12345`）
2. **集合运算**: 
   - `missing_in_local` = arXiv ∩ ¬Local
   - `extra_in_local` = Local ∩ ¬arXiv
3. **统计计算**: 分类级别和整体匹配率

### 输出格式

#### JSON 报告
```json
{
  "date": "2024-11-25",
  "summary": {
    "total_arxiv": 156,
    "total_local": 156,
    "total_matched": 156,
    "overall_match_rate": 100.0
  },
  "categories": {
    "cs.AI": {
      "arxiv_count": 23,
      "local_count": 23,
      "matched_count": 23,
      "match_rate": 100.0,
      "missing_ids": [],
      "extra_ids": []
    }
  }
}
```

#### Markdown 报告
生成的 Markdown 文件包含：
- 格式化的表格
- 可点击的 arXiv 链接
- 清晰的状态指示器（✅/⚠️）

## ⚠️ 注意事项

### 1. API 使用限制

- **速率限制**: 至少 3 秒/请求（已自动处理）
- **单次查询上限**: 1000 条结果（已自动分页）
- **日期过滤**: 需要后处理（API 不直接支持按发布日期过滤）

### 2. 数据要求

本地数据文件期望格式：

```
papers_data/
├── cs.AI/
│   └── papers_2024-11-25_100percent.json
├── cs.CV/
│   └── papers_2024-11-25_100percent.json
└── ...
```

每个 JSON 文件：
```json
{
  "metadata": {...},
  "papers": [
    {
      "arxiv_id": "2411.12345v1",
      "title": "...",
      "abstract": "...",
      "authors": [...],
      "categories": [...]
    }
  ]
}
```

### 3. 性能考虑

- **多分类查询**: 每个分类单独查询，可能耗时较长
- **大量结果**: 超过 1000 条需要多次请求
- **网络延迟**: 3 秒/请求，10 个分类约需 30-60 秒

## 🔧 故障排除

### 常见问题

**Q: 导入错误 `ModuleNotFoundError`**
```bash
# 确保在项目根目录运行
cd /home/hy/project/papers.cool/arxiv-paper-curator
python examples/compare_local_with_arxiv.py --date 2024-11-25
```

**Q: 本地文件未找到**
```bash
# 先运行抓取脚本
python src/scripts/fetch_daily_papers_100percent.py --date 2024-11-25
```

**Q: API 请求超时**
```bash
# 增加请求间隔
python examples/compare_local_with_arxiv.py --date 2024-11-25 --delay 5.0
```

**Q: 昨天数据为空**
```
# arXiv 周末可能不发布新论文，尝试使用工作日日期
python examples/compare_local_with_arxiv.py --date 2024-11-22  # 周五
```

## 📈 最佳实践

### 1. 选择合适的验证时机

```bash
# ❌ 不推荐：当天数据可能不完整
python examples/compare_local_with_arxiv.py --date $(date +%Y-%m-%d)

# ✅ 推荐：昨天或更早的数据（工作日）
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
python examples/compare_local_with_arxiv.py --date $YESTERDAY
```

### 2. 定期自动化验证

```bash
# 添加到 crontab
# 每天早上 8 点验证昨天的数据
0 8 * * * cd /path/to/project && python examples/compare_local_with_arxiv.py --date $(date -d "yesterday" +\%Y-\%m-\%d) --output ./daily_validation
```

### 3. 处理验证失败

```bash
# 1. 查看详细报告
cat comparison_results/comparison_report_2024-11-25.md

# 2. 重新抓取缺失的论文
python src/scripts/fetch_daily_papers_100percent.py --date 2024-11-25

# 3. 再次验证
python examples/compare_local_with_arxiv.py --date 2024-11-25
```

## 🎓 进阶用法

### 自定义验证逻辑

```python
from src.scripts.arxiv_advanced_search import (
    ArxivAdvancedSearch,
    compare_with_local_data
)

# 创建自定义验证流程
def custom_validation(date, threshold=95):
    searcher = ArxivAdvancedSearch()
    
    # 1. 搜索 arXiv
    arxiv_results = searcher.search_by_date_and_category(
        date=date,
        categories=["cs.AI", "cs.CV"]
    )
    
    # 2. 加载本地数据
    local_data = load_local_data(date)
    
    # 3. 对比
    report = compare_with_local_data(arxiv_results, local_data, date)
    
    # 4. 自定义处理
    if report['summary']['overall_match_rate'] < threshold:
        send_alert(report)
        trigger_refetch(date)
    
    return report
```

### 集成到 Web 界面

```python
# 在 Streamlit 应用中
import streamlit as st
from src.scripts.arxiv_advanced_search import ArxivAdvancedSearch

st.title("数据完整性验证")

date = st.date_input("选择日期")
categories = st.multiselect("选择分类", ["cs.AI", "cs.CV", "cs.LG"])

if st.button("验证数据"):
    with st.spinner("正在验证..."):
        searcher = ArxivAdvancedSearch()
        results = searcher.search_by_date_and_category(
            date=date,
            categories=categories
        )
        
        # 对比和显示结果
        # ...
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可

MIT License

## 📞 支持

- 查看 [QUICKSTART.md](./QUICKSTART.md) 快速上手
- 查看 [SUMMARY.md](./SUMMARY.md) 了解完整功能
- 查看 [README_comparison.md](./README_comparison.md) 了解详细用法

---

**Happy Searching! 🎉**

