# arXiv 数据完整性对比工具

这个工具可以帮助你验证本地获取的 arXiv 论文数据与 arXiv 官方 API 搜索结果的一致性。

## 功能特点

✅ **完整对比**：对比本地数据与 arXiv 官方搜索结果  
✅ **多维度分析**：按分类、日期、关键词进行对比  
✅ **详细报告**：生成 JSON 和 Markdown 格式的对比报告  
✅ **缺失检测**：精确识别缺失或额外的论文  
✅ **匹配率统计**：计算整体和分类级别的匹配率

## 快速开始

### 1. 基本用法

对比指定日期的所有分类：

```bash
cd /home/hy/project/papers.cool/arxiv-paper-curator
python examples/compare_local_with_arxiv.py --date 2024-11-25
```

### 2. 指定分类对比

只对比特定分类（如 cs.AI 和 cs.CV）：

```bash
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --categories cs.AI cs.CV
```

### 3. 使用关键词过滤

对比包含特定关键词的论文：

```bash
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --keywords "large language model"
```

### 4. 保存对比结果

将对比结果保存到文件：

```bash
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --output ./comparison_results
```

这会生成以下文件：
- `arxiv_results_2024-11-25.json` - arXiv 官方搜索结果
- `comparison_report_2024-11-25.json` - JSON 格式对比报告
- `comparison_report_2024-11-25.md` - Markdown 格式对比报告

### 5. 完整示例

```bash
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --categories cs.AI cs.CL cs.CV cs.LG \
    --keywords "large language model" \
    --local-data-dir ./papers_data \
    --output ./comparison_results \
    --delay 3.5
```

## 参数说明

| 参数 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `--date` | 目标日期 (YYYY-MM-DD) | - | ✅ |
| `--categories` | 分类列表 | 所有 AI 相关分类 | ❌ |
| `--keywords` | 搜索关键词 | None | ❌ |
| `--local-data-dir` | 本地数据目录 | `./papers_data` | ❌ |
| `--output` | 输出目录 | None | ❌ |
| `--delay` | API 请求间隔（秒） | 3.0 | ❌ |

## 输出示例

### 控制台输出

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
    arXiv: 45, Local: 45, Matched: 45 (100.0%)

  cs.LG:
    arXiv: 88, Local: 87, Matched: 87 (98.9%)
    ⚠️  Missing in local (1):
       - 2411.12345

================================================================================
```

### JSON 报告格式

```json
{
  "date": "2024-11-25",
  "summary": {
    "total_arxiv": 156,
    "total_local": 155,
    "total_matched": 155,
    "total_missing_in_local": 1,
    "total_extra_in_local": 0,
    "overall_match_rate": 99.36
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

## 使用场景

### 场景 1: 验证每日数据抓取的完整性

```bash
# 先运行每日抓取
python papers.cool/arxiv-paper-curator/src/scripts/fetch_daily_papers_100percent.py \
    --date 2024-11-25

# 然后验证数据完整性
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --output ./validation_reports
```

### 场景 2: 检查特定关键词的覆盖率

```bash
# 检查 "large language model" 相关论文的覆盖情况
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --keywords "large language model" \
    --output ./coverage_reports
```

### 场景 3: 定期数据质量审计

创建一个脚本定期运行对比：

```bash
#!/bin/bash
# daily_validation.sh

YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

python examples/compare_local_with_arxiv.py \
    --date $YESTERDAY \
    --output ./validation_reports/$YESTERDAY

# 检查匹配率
# 如果匹配率 < 95%，发送告警邮件
```

## 直接使用 ArxivAdvancedSearch 类

如果你想在自己的代码中使用搜索功能：

```python
from src.scripts.arxiv_advanced_search import ArxivAdvancedSearch
from datetime import datetime

# 创建搜索客户端
searcher = ArxivAdvancedSearch(delay_seconds=3.0)

# 搜索特定日期和分类的论文
results = searcher.search(
    keywords="large language model",
    categories=["cs.AI", "cs.CL"],
    date_from=datetime(2024, 11, 25),
    date_to=datetime(2024, 11, 25),
    max_results=1000
)

print(f"Found {len(results)} papers")
for paper in results:
    print(f"- {paper['arxiv_id']}: {paper['title']}")
```

## 常见问题

### Q1: 为什么会有 "Extra in local" 的论文？

**A:** 这通常是因为：
1. 论文被 cross-list 到多个分类，你的本地抓取可能在多个分类中都保存了
2. 论文后来被撤回或重新分类
3. 本地数据包含了更新版本，而搜索时间点不同

### Q2: API 请求速度很慢怎么办？

**A:** arXiv 要求 API 请求间隔至少 3 秒。你可以：
1. 减少要对比的分类数量
2. 使用 `--delay` 参数调整间隔时间（不要低于 3 秒）
3. 分批次进行对比

### Q3: 如何处理缺失的论文？

**A:** 如果发现缺失论文：
1. 检查对比报告中的 `missing_ids`
2. 重新运行 `fetch_daily_papers_100percent.py` 抓取该日期的数据
3. 或使用自定义 ID 列表功能单独抓取缺失的论文

### Q4: 匹配率多少算正常？

**A:** 
- **100%**: 完美匹配 ✅
- **95-99%**: 良好，可能有少量时间差异或版本更新 ✓
- **<95%**: 需要检查抓取流程 ⚠️

## 技术细节

### arXiv API 限制

- **速率限制**: 每 3 秒最多 1 个请求
- **单次最大结果**: 1000 条
- **日期过滤**: 使用论文的 `submittedDate`

### 对比逻辑

1. 移除版本号后对比 arXiv ID（如 `2411.12345v1` → `2411.12345`）
2. 计算集合差异：
   - `missing_in_local` = arXiv 有但本地没有
   - `extra_in_local` = 本地有但 arXiv 搜索结果中没有
3. 按分类分别统计

### 本地数据格式要求

期望的本地数据文件路径：
```
papers_data/
  ├── cs.AI/
  │   └── papers_2024-11-25_100percent.json
  ├── cs.CV/
  │   └── papers_2024-11-25_100percent.json
  └── ...
```

每个 JSON 文件格式：
```json
{
  "metadata": {...},
  "papers": [
    {
      "arxiv_id": "2411.12345v1",
      "title": "...",
      "abstract": "...",
      "authors": [...],
      "categories": [...],
      "published_date": "2024-11-25"
    }
  ]
}
```

## 贡献

如果你发现问题或有改进建议，欢迎提交 Issue 或 Pull Request！

## 许可

MIT License

