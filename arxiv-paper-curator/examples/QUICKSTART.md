# 快速开始指南

## 🎯 目标

对比本地 arXiv 数据与官方搜索结果，验证数据完整性。

## 📋 前置要求

```bash
# 确保已安装依赖
pip install requests

# 确保已有本地数据（通过 fetch_daily_papers_100percent.py 获取）
```

## 🚀 三步对比

### 第一步：快速测试（可选）

验证 arXiv API 连接是否正常：

```bash
cd /home/hy/project/papers.cool/arxiv-paper-curator
python examples/quick_test.py
```

预期输出：显示昨天的论文搜索结果

### 第二步：运行对比

对比指定日期的数据：

```bash
python examples/compare_local_with_arxiv.py --date 2024-11-25
```

### 第三步：查看结果

查看控制台输出的对比报告，包括：
- 总体匹配率
- 各分类匹配情况
- 缺失/额外的论文 ID

## 📊 常用命令

### 1. 完整对比（推荐）

```bash
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --output ./comparison_results
```

生成文件：
- `comparison_report_2024-11-25.json` - JSON 格式报告
- `comparison_report_2024-11-25.md` - Markdown 格式报告
- `arxiv_results_2024-11-25.json` - arXiv 官方搜索原始结果

### 2. 对比特定分类

```bash
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --categories cs.AI cs.CV
```

### 3. 搜索特定关键词

```bash
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --keywords "large language model"
```

## 🔍 结果解读

### 完美匹配 (100%)
```
✅ Perfect match! Your local data is 100% complete.
```
→ 本地数据完整，无需操作

### 高匹配率 (95-99%)
```
✓ Good match rate (98.5%). Minor discrepancies detected.
  ⚠️  Missing in local (2):
     - 2411.12345
     - 2411.12346
```
→ 可能是时间差异，建议重新抓取这些论文

### 低匹配率 (<95%)
```
⚠️  Match rate is 87.3%. Please check your fetch process.
  ⚠️  Missing in local (15):
     - 2411.12345
     - ...
```
→ 抓取过程可能有问题，需要检查日志并重新运行

## 🛠️ 故障排除

### 问题 1: "Local file not found"

```
⚠ File not found: ./papers_data/cs.AI/papers_2024-11-25_100percent.json
```

**解决方案**：
```bash
# 先运行抓取脚本
python papers.cool/arxiv-paper-curator/src/scripts/fetch_daily_papers_100percent.py \
    --date 2024-11-25
```

### 问题 2: API 请求超时

```
Error fetching results: timeout
```

**解决方案**：
```bash
# 增加请求间隔
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --delay 5.0
```

### 问题 3: 导入错误

```
ModuleNotFoundError: No module named 'src'
```

**解决方案**：
```bash
# 确保在项目根目录运行
cd /home/hy/project/papers.cool/arxiv-paper-curator
python examples/compare_local_with_arxiv.py --date 2024-11-25
```

## 📈 实际使用示例

### 示例 1: 验证昨天的数据

```bash
# 设置昨天的日期
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

# 运行对比
python examples/compare_local_with_arxiv.py \
    --date $YESTERDAY \
    --output ./validation_reports/$YESTERDAY
```

### 示例 2: 检查 LLM 相关论文

```bash
# 对比 "large language model" 相关论文
python examples/compare_local_with_arxiv.py \
    --date 2024-11-25 \
    --keywords "large language model" \
    --categories cs.AI cs.CL cs.LG \
    --output ./llm_papers_validation
```

### 示例 3: 批量验证多个日期

```bash
#!/bin/bash
# validate_week.sh

for i in {1..7}; do
    DATE=$(date -d "$i days ago" +%Y-%m-%d)
    echo "Validating $DATE..."
    
    python examples/compare_local_with_arxiv.py \
        --date $DATE \
        --output ./weekly_validation/$DATE
    
    sleep 5  # 避免频繁请求
done
```

## 🎓 进阶使用

### 在 Python 代码中使用

```python
from src.scripts.arxiv_advanced_search import ArxivAdvancedSearch
from datetime import datetime

# 创建搜索客户端
searcher = ArxivAdvancedSearch()

# 搜索指定日期和关键词
results = searcher.search(
    keywords="transformer",
    categories=["cs.AI"],
    date_from=datetime(2024, 11, 25),
    date_to=datetime(2024, 11, 25)
)

# 处理结果
for paper in results:
    print(f"{paper['arxiv_id']}: {paper['title']}")
```

### 自定义对比逻辑

```python
from src.scripts.arxiv_advanced_search import compare_with_local_data
import json

# 加载数据
with open('arxiv_results.json') as f:
    arxiv_data = json.load(f)

with open('local_papers.json') as f:
    local_data = json.load(f)

# 执行对比
report = compare_with_local_data(
    arxiv_data, 
    local_data, 
    datetime(2024, 11, 25)
)

# 自定义处理
if report['summary']['overall_match_rate'] < 95:
    send_alert_email(report)
```

## 📚 更多信息

- 详细文档：[README_comparison.md](./README_comparison.md)
- API 文档：查看 `arxiv_advanced_search.py` 的 docstrings
- arXiv API 官方文档：https://arxiv.org/help/api/

## 💡 提示

1. **遵守 API 限制**：arXiv 要求请求间隔 ≥3 秒
2. **选择合适的日期**：建议对比昨天或更早的数据（当天数据可能不完整）
3. **保存对比报告**：使用 `--output` 参数保存详细报告以便后续分析
4. **定期验证**：建议每周运行一次验证脚本

## ❓ 需要帮助？

- 检查日志输出中的详细错误信息
- 查看生成的 Markdown 报告了解详细差异
- 确认本地数据文件格式正确

