# 每日 arXiv 论文自动获取

自动获取指定分类的每日 arXiv 论文，支持持续运行和错误重试。

## 功能特点

- ✅ **支持多个分类**：同时获取多个 arXiv 分类的论文（cs.AI, cs.LG, cs.CV 等）
- ✅ **完整分页获取**：使用 `fetch_all_papers_in_date_range` 函数自动处理分页，获取所有论文
- ✅ **错误重试**：API 失败时自动重试，确保最终获取成功
- ✅ **持续运行模式**：定期检查新论文，保持数据最新
- ✅ **精简数据格式**：仅保存必要信息（标题/作者/摘要/分类/URL），不下载 PDF
- ✅ **去重处理**：自动移除重复论文（同一论文可能属于多个分类）

## 快速开始

### 1. 获取特定日期的论文（单次运行）

```bash
# 获取今天的论文
python -m src.scripts.fetch_daily_papers

# 获取特定日期的论文
python -m src.scripts.fetch_daily_papers --date 2025-11-13

# 指定输出目录
python -m src.scripts.fetch_daily_papers --date 2025-11-13 --output-dir ./my_papers
```

### 2. 持续运行模式（自动定期获取）

```bash
# 每 6 小时检查一次新论文（默认）
python -m src.scripts.fetch_daily_papers

# 自定义检查间隔（每 2 小时）
python -m src.scripts.fetch_daily_papers --interval 2

# 后台运行（Linux/Mac）
nohup python -m src.scripts.fetch_daily_papers > fetch_papers.log 2>&1 &
```

### 3. 指定特定分类

```bash
# 只获取 AI 和机器学习相关论文
python -m src.scripts.fetch_daily_papers --categories cs.AI cs.LG stat.ML

# 只获取计算机视觉论文
python -m src.scripts.fetch_daily_papers --categories cs.CV
```

## 命令行参数

```
--output-dir DIR     输出目录（默认：./papers_data）
--categories CAT     要获取的分类列表（默认：所有分类）
--date YYYY-MM-DD    获取特定日期的论文（不提供则持续运行）
--interval HOURS     持续模式下的检查间隔小时数（默认：6）
```

## 支持的分类

脚本默认支持以下 arXiv 分类（与 streamlit_app.py 保持一致）：

- `cs.AI` - Artificial Intelligence
- `cs.CL` - Computation and Language (NLP)
- `cs.CV` - Computer Vision
- `cs.LG` - Machine Learning
- `cs.NE` - Neural and Evolutionary Computing
- `cs.CC` - Computational Complexity
- `stat.ML` - Statistics - Machine Learning

## 输出格式

论文数据保存为 JSON 文件，命名格式：`papers_YYYY-MM-DD.json`

每篇论文包含以下字段：

```json
{
  "arxiv_id": "2411.12345",
  "title": "Paper Title",
  "authors": ["Author 1", "Author 2"],
  "abstract": "Paper abstract...",
  "categories": ["cs.AI", "cs.LG"],
  "published_date": "2025-11-13T08:30:00Z",
  "url": "https://arxiv.org/abs/2411.12345",
  "pdf_url": "https://arxiv.org/pdf/2411.12345.pdf"
}
```

## 核心实现

### ArxivClient 新增功能

#### 1. ArxivSearchResult Schema

新增了 `ArxivSearchResult` 类来存储搜索元数据：

```python
class ArxivSearchResult(BaseModel):
    papers: List[ArxivPaper]       # 论文列表
    total_results: int              # 总结果数
    start_index: int                # 起始索引
    items_per_page: int             # 每页数量
    search_query: str               # 搜索查询
```

#### 2. fetch_papers 方法更新

现在返回 `ArxivSearchResult` 而不是 `List[ArxivPaper]`，提供完整的元数据：

```python
result = await client.fetch_papers(
    max_results=100,
    start=0,
    from_date="20251113",
    to_date="20251113"
)
print(f"Found {result.total_results} papers, fetched {len(result.papers)}")
```

#### 3. fetch_all_papers_in_date_range 方法

新增的核心方法，自动处理分页获取所有论文：

```python
papers, results = await client.fetch_all_papers_in_date_range(
    from_date="20251113",
    to_date="20251113",
    max_per_page=100,           # 每页最多获取 100 篇
    max_total_papers=None,      # 无限制，获取所有论文
    sort_by="submittedDate",
    sort_order="descending"
)
```

**特点：**
- ✅ 自动分页，获取所有可用论文
- ✅ 智能判断最后一页（返回数量 < max_per_page）
- ✅ 自动重试 API 错误（超时、网络问题等）
- ✅ 10 秒重试延迟，避免过度请求
- ✅ 安全限制（最多 10000 条，防止无限循环）
- ✅ 详细日志记录进度

## 使用示例

### Python 代码示例

```python
import asyncio
from datetime import datetime
from src.config import ArxivSettings
from src.services.arxiv.client import ArxivClient

async def fetch_today_papers():
    """获取今天的 AI 论文"""
    # 创建客户端
    settings = ArxivSettings(search_category="cs.AI")
    client = ArxivClient(settings)
    
    # 获取今天的所有论文
    today = datetime.now().strftime("%Y%m%d")
    papers, results = await client.fetch_all_papers_in_date_range(
        from_date=today,
        to_date=today,
        max_per_page=100,
    )
    
    print(f"Total papers: {len(papers)}")
    
    # 处理论文
    for paper in papers:
        print(f"- {paper.title}")
        print(f"  Authors: {', '.join(paper.authors[:3])}")
        print(f"  URL: https://arxiv.org/abs/{paper.arxiv_id}")
        print()

# 运行
asyncio.run(fetch_today_papers())
```

### 与 Streamlit 应用集成

生成的 JSON 文件可以直接被 `streamlit_app.py` 读取：

```python
# streamlit_app.py 中的 load_papers_from_json 函数
# 会自动读取 papers_YYYY-MM-DD.json 文件
papers = load_papers_from_json("2025-11-13")
```

## 错误处理

脚本内置了完善的错误处理机制：

1. **API 超时/失败**：自动重试最多 5 次，指数退避延迟
2. **网络中断**：持续模式下会等待并继续尝试
3. **数据去重**：相同论文（arxiv_id）只保存一次
4. **文件检查**：避免重复获取已有日期的数据

## 监控和日志

脚本会输出详细的日志信息：

```
2025-11-13 13:38:27 - __main__ - INFO - Starting continuous mode (checking every 6 hours)
2025-11-13 13:38:27 - __main__ - INFO - ================================================================================
2025-11-13 13:38:27 - __main__ - INFO - Starting daily fetch for 2025-11-13
2025-11-13 13:38:27 - __main__ - INFO - ================================================================================
2025-11-13 13:38:30 - src.services.arxiv.client - INFO - Fetched 100 papers (total so far: 100/523), next start: 100
2025-11-13 13:38:35 - src.services.arxiv.client - INFO - Fetched 100 papers (total so far: 200/523), next start: 200
...
2025-11-13 13:39:00 - __main__ - INFO - Saved 523 unique papers to ./papers_data/papers_2025-11-13.json
```

## 生产环境部署

### 使用 systemd（Linux）

创建服务文件 `/etc/systemd/system/arxiv-fetcher.service`：

```ini
[Unit]
Description=ArXiv Daily Papers Fetcher
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/arxiv-paper-curator
ExecStart=/usr/bin/python3 -m src.scripts.fetch_daily_papers --output-dir /data/papers
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable arxiv-fetcher
sudo systemctl start arxiv-fetcher
sudo systemctl status arxiv-fetcher
```

### 使用 Docker

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "src.scripts.fetch_daily_papers", "--output-dir", "/data/papers"]
```

运行：

```bash
docker build -t arxiv-fetcher .
docker run -d --name arxiv-fetcher -v /path/to/papers:/data/papers arxiv-fetcher
```

## 性能优化建议

1. **并发获取多个分类**：脚本默认使用 `asyncio.gather()` 并发获取所有分类
2. **合理设置页面大小**：`max_per_page=100` 是推荐值（arXiv 限制最大 1000）
3. **调整检查间隔**：根据需求调整 `--interval`，避免过于频繁的 API 调用
4. **速率限制遵守**：脚本自动遵守 arXiv 的 3 秒速率限制

## 故障排查

### 问题：API 持续超时

```bash
# 检查网络连接
curl -I https://export.arxiv.org/api/query

# 增加重试次数（修改脚本中的 MAX_RETRY_ATTEMPTS）
# 或者增加检查间隔
python -m src.scripts.fetch_daily_papers --interval 12
```

### 问题：没有获取到论文

- 检查日期格式是否正确（YYYYMMDD）
- 验证分类代码是否正确
- 查看日志中的错误信息

### 问题：重复运行导致重复文件

脚本会自动跳过已存在的日期文件。如需重新获取：

```bash
rm papers_data/papers_YYYY-MM-DD.json
python -m src.scripts.fetch_daily_papers --date YYYY-MM-DD
```

## 未来改进

- [ ] 支持增量更新（仅获取新增论文）
- [ ] 添加 Web 界面监控脚本运行状态
- [ ] 支持自定义过滤条件（关键词、作者等）
- [ ] 集成通知系统（邮件、Slack 等）
- [ ] 支持数据库存储（而不是 JSON 文件）

## 相关文件

- `src/services/arxiv/client.py` - ArXiv API 客户端
- `src/schemas/arxiv/paper.py` - 论文数据结构定义
- `src/config.py` - 配置管理
- `frontend/streamlit_app.py` - Streamlit 前端应用

## 技术支持

如有问题，请检查：
1. 日志输出
2. arXiv API 状态：https://status.arxiv.org/
3. 网络连接和防火墙设置
