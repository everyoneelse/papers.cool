# Cool Papers Backend

完整的后端实现，用于 **Cool Papers** 沉浸式论文发现平台。

## 功能特性

### 🕷️ 多源论文爬虫
- **ArXiv**: 支持所有分类，实时获取最新论文
- **OpenReview**: 会议论文获取
- **ACL Anthology**: ACL系列会议论文
- **PMLR**: 机器学习会议论文集

### 📊 数据管理
- SQLAlchemy ORM 异步数据库操作
- 支持 SQLite（开发）和 PostgreSQL（生产）
- 论文元数据存储和检索
- 用户活动追踪

### 🔍 全文搜索
- 基于 Tantivy 的 BM25 搜索引擎
- 支持标题、摘要、全文搜索
- 分类和会议过滤
- 搜索建议功能

### 📄 PDF 处理
- 自动从 PDF 提取全文
- PDF 缓存机制
- 支持多种论文源的 PDF

### 📡 API 接口
- RESTful API 设计
- 自动生成 API 文档（Swagger）
- RSS/Atom Feed 支持
- CORS 支持

### ⚡ 性能优化
- 异步 I/O (asyncio + httpx)
- 请求速率限制
- 数据缓存
- 批量操作优化

## 技术栈

- **Web Framework**: FastAPI
- **Database**: SQLAlchemy (async) + SQLite/PostgreSQL
- **Search Engine**: Tantivy (BM25)
- **PDF Processing**: PyMuPDF
- **HTTP Client**: httpx, aiohttp
- **HTML Parsing**: PyQuery, BeautifulSoup
- **Feed Generation**: feedgen

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、API密钥等
```

### 3. 初始化数据库

数据库会在首次启动时自动初始化。

### 4. 启动服务

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问 API 文档

打开浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 论文操作

- `GET /papers/arxiv/{paper_id}` - 获取单篇 ArXiv 论文
- `GET /papers/arxiv/list/{category}` - 获取分类论文列表
- `GET /papers/arxiv/combined` - 获取多分类组合（支持排除）
- `GET /papers/venue/{venue_id}` - 获取会议论文
- `GET /papers/{source}/{paper_id}` - 获取任意源论文
- `POST /papers/{paper_id}/click` - 记录点击统计
- `GET /papers/{paper_id}/full_text` - 提取 PDF 全文

### 搜索

- `GET /search/` - 全文搜索
- `GET /search/arxiv` - ArXiv API 搜索
- `GET /search/suggestions` - 搜索建议

### RSS/Atom Feeds

- `GET /feeds/arxiv/{category}` - ArXiv 分类订阅
- `GET /feeds/venue/{venue_id}` - 会议订阅
- `GET /feeds/latest` - 最新论文订阅

## 项目结构

```
backend/
├── main.py                 # FastAPI 应用入口
├── config.py              # 配置管理
├── database.py            # 数据库连接
├── models.py              # SQLAlchemy 模型
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量示例
├── api/                  # API 路由
│   ├── papers.py         # 论文相关接口
│   ├── search.py         # 搜索接口
│   └── feeds.py          # Feed 订阅接口
├── scrapers/             # 爬虫模块
│   ├── base_scraper.py   # 爬虫基类
│   ├── arxiv_scraper.py  # ArXiv 爬虫
│   ├── openreview_scraper.py
│   ├── acl_scraper.py
│   └── pmlr_scraper.py
└── utils/                # 工具模块
    ├── pdf_processor.py  # PDF 处理
    └── search_engine.py  # 搜索引擎
```

## 使用示例

### 获取 ArXiv 论文

```python
import httpx

# 获取单篇论文
response = httpx.get("http://localhost:8000/papers/arxiv/2401.12345")
paper = response.json()

# 获取分类列表
response = httpx.get("http://localhost:8000/papers/arxiv/list/cs.AI")
papers = response.json()

# 多分类组合（cs.AI 或 cs.LG，但排除 cs.CY）
response = httpx.get(
    "http://localhost:8000/papers/arxiv/combined",
    params={"include": "cs.AI,cs.LG", "exclude": "cs.CY"}
)
```

### 搜索论文

```python
# 全文搜索
response = httpx.get(
    "http://localhost:8000/search/",
    params={"query": "transformer attention", "max_results": 50}
)
results = response.json()
```

### 订阅 Feed

在 RSS 阅读器中添加：
- `http://localhost:8000/feeds/arxiv/cs.AI`
- `http://localhost:8000/feeds/venue/ICML.2024`
- `http://localhost:8000/feeds/latest`

## 部署

### 使用 Docker

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建并运行：

```bash
docker build -t coolpapers-backend .
docker run -p 8000:8000 -v ./data:/app/data coolpapers-backend
```

### 使用 Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/coolpapers
    depends_on:
      - db
    volumes:
      - ./data:/app/data
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: coolpapers
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

运行：

```bash
docker-compose up -d
```

### 生产环境建议

1. **使用 PostgreSQL** 而不是 SQLite
2. **配置 Redis** 用于缓存
3. **使用 Nginx** 作为反向代理
4. **启用 HTTPS** (Let's Encrypt)
5. **配置日志轮转**
6. **设置监控和告警** (Prometheus + Grafana)
7. **使用 Gunicorn + Uvicorn Workers**:

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 定时任务

为了自动更新论文，可以设置定时任务（cron）：

```python
# scripts/update_arxiv.py
import asyncio
from datetime import datetime
from scrapers import ArxivScraper
from database import AsyncSessionLocal
from models import Paper

async def update_arxiv_papers():
    """更新 ArXiv 论文"""
    scraper = ArxivScraper()
    categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV"]
    
    async with AsyncSessionLocal() as db:
        for category in categories:
            papers = await scraper.fetch_latest(category)
            for paper_data in papers:
                paper = Paper(**paper_data)
                db.add(paper)
        await db.commit()

if __name__ == "__main__":
    asyncio.run(update_arxiv_papers())
```

Crontab 配置（每天早上 8 点更新）：

```bash
0 8 * * * cd /path/to/backend && python scripts/update_arxiv.py
```

## 性能优化

1. **数据库索引**: 已在模型中定义关键索引
2. **批量操作**: 使用 `add_papers_batch` 批量插入
3. **缓存**: 启用 Redis 缓存热门查询
4. **异步操作**: 所有 I/O 操作使用 async/await
5. **连接池**: 配置数据库连接池大小

## 故障排查

### 数据库连接错误
```bash
# 检查数据库文件权限
ls -la coolpapers.db

# 重新初始化数据库
rm coolpapers.db
python main.py
```

### ArXiv 爬取失败
- 检查网络连接
- 确认 ArXiv 是否可访问
- 调整 `ARXIV_RATE_LIMIT` 避免被限流

### 搜索索引问题
```bash
# 清除并重建索引
rm -rf search_index/
# 重启应用会自动重建
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black .
isort .
```

### 类型检查

```bash
mypy .
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- GitHub: https://github.com/yourusername/coolpapers
- Email: your.email@example.com
