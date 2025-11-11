# Cool Papers Backend - 完整实现说明

## 🎉 已完成！

我已经为 Cool Papers 项目实现了**完整的后端系统**，包括爬虫、数据处理、API 服务等所有核心功能。

## 📁 项目结构

```
backend/
├── main.py                    # FastAPI 主应用
├── config.py                  # 配置管理
├── database.py                # 数据库连接
├── models.py                  # 数据模型
├── requirements.txt           # Python 依赖
├── README.md                  # 详细文档
├── Dockerfile                 # Docker 镜像
├── docker-compose.yml         # Docker Compose 配置
├── nginx.conf                 # Nginx 反向代理配置
├── .env.example              # 环境变量示例
├── .gitignore                # Git 忽略文件
│
├── api/                      # API 路由模块
│   ├── papers.py            # 论文相关接口
│   ├── search.py            # 搜索接口
│   └── feeds.py             # RSS/Atom 订阅
│
├── scrapers/                 # 爬虫模块
│   ├── base_scraper.py      # 爬虫基类
│   ├── arxiv_scraper.py     # ArXiv 爬虫
│   ├── openreview_scraper.py # OpenReview 爬虫
│   ├── acl_scraper.py       # ACL Anthology 爬虫
│   └── pmlr_scraper.py      # PMLR 爬虫
│
├── utils/                    # 工具模块
│   ├── pdf_processor.py     # PDF 文本提取
│   └── search_engine.py     # 全文搜索引擎
│
├── scripts/                  # 脚本工具
│   └── update_papers.py     # 定时更新脚本
│
└── tests/                    # 测试文件
    ├── test_scrapers.py
    └── test_api.py
```

## ⚡ 核心功能

### 1. 多源论文爬虫 🕷️

#### ArXiv 爬虫 (`scrapers/arxiv_scraper.py`)
- ✅ 通过 ArXiv API 获取单篇论文
- ✅ 获取特定分类的最新论文列表
- ✅ 支持多分类组合（并集）
- ✅ 支持分类排除（差集）
- ✅ 全文搜索功能
- ✅ 论文 ID 格式规范化（支持新旧格式）
- ✅ 速率限制（避免被封）

#### OpenReview 爬虫 (`scrapers/openreview_scraper.py`)
- ✅ 获取单篇 OpenReview 论文
- ✅ 获取特定会议的所有论文
- ✅ 提取关键词、TL;DR 等元数据

#### ACL Anthology 爬虫 (`scrapers/acl_scraper.py`)
- ✅ 获取 ACL 系列会议论文
- ✅ 支持按会议和年份查询

#### PMLR 爬虫 (`scrapers/pmlr_scraper.py`)
- ✅ 获取机器学习会议论文集
- ✅ 支持按卷号（volume）查询

### 2. 数据存储 💾

#### 数据库模型 (`models.py`)
- **Paper**: 论文主表
  - 基本信息：标题、作者、摘要
  - 链接：论文页面、PDF 地址
  - 分类和会议信息
  - 全文（从 PDF 提取）
  - 统计：浏览数、点击数
  
- **UserActivity**: 用户行为追踪
  - 点击记录、星标等

- **CachedSummary**: AI 摘要缓存
  - 中英文摘要
  - FAQ 问答

- **SearchLog**: 搜索日志
  - 用于分析和推荐

- **Feed**: RSS/Atom 订阅元数据

### 3. PDF 处理 📄 (`utils/pdf_processor.py`)
- ✅ 从 URL 下载 PDF
- ✅ 使用 PyMuPDF 提取全文
- ✅ 文本清理和格式化
- ✅ 本地缓存机制
- ✅ 文件大小限制

### 4. 全文搜索 🔍 (`utils/search_engine.py`)
- ✅ 基于 Tantivy 的 BM25 搜索引擎
- ✅ 支持标题、摘要、全文搜索
- ✅ 按分类、会议过滤
- ✅ 批量索引更新
- ✅ 搜索结果相关性排序

### 5. REST API 接口 🌐

#### 论文接口 (`api/papers.py`)
```
GET  /papers/arxiv/{paper_id}              # 获取单篇 ArXiv 论文
GET  /papers/arxiv/list/{category}         # 获取分类列表
GET  /papers/arxiv/combined                # 多分类组合查询
GET  /papers/venue/{venue_id}              # 获取会议论文
GET  /papers/{source}/{paper_id}           # 通用论文获取
POST /papers/{paper_id}/click              # 记录点击
GET  /papers/{paper_id}/full_text          # 提取 PDF 全文
```

#### 搜索接口 (`api/search.py`)
```
GET /search/                               # 全文搜索
GET /search/arxiv                          # ArXiv API 搜索
GET /search/suggestions                    # 搜索建议
```

#### 订阅接口 (`api/feeds.py`)
```
GET /feeds/arxiv/{category}                # ArXiv 分类订阅
GET /feeds/venue/{venue_id}                # 会议订阅
GET /feeds/latest                          # 最新论文订阅
```

## 🚀 快速开始

### 方式 1：本地运行

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动服务
python main.py

# 访问 API 文档
# http://localhost:8000/docs
```

### 方式 2：Docker 部署

```bash
cd backend

# 构建并启动所有服务（API + PostgreSQL + Redis + Nginx）
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

## 📊 使用示例

### Python 客户端

```python
import httpx

# 获取论文
response = httpx.get("http://localhost:8000/papers/arxiv/2005.14165")
paper = response.json()
print(paper['title'])

# 搜索论文
response = httpx.get(
    "http://localhost:8000/search/",
    params={"query": "transformer attention", "max_results": 50}
)
results = response.json()

# 获取分类列表（支持多分类组合和排除）
response = httpx.get(
    "http://localhost:8000/papers/arxiv/combined",
    params={
        "include": "cs.AI,cs.LG",  # 包含 cs.AI 或 cs.LG
        "exclude": "cs.CY"          # 排除 cs.CY
    }
)
```

### 订阅 Feed

在你的 RSS 阅读器中添加：
- `http://localhost:8000/feeds/arxiv/cs.AI`
- `http://localhost:8000/feeds/venue/ICML.2024`
- `http://localhost:8000/feeds/latest`

## 🔄 定时更新

使用提供的脚本定时更新论文：

```bash
# 手动运行
python scripts/update_papers.py

# 使用 cron 每天自动更新（早上 8 点）
0 8 * * * cd /path/to/backend && python scripts/update_papers.py
```

## 🛠️ 技术特性

### 性能优化
- ✅ 异步 I/O（asyncio + httpx）
- ✅ 数据库连接池
- ✅ 批量数据库操作
- ✅ PDF 缓存
- ✅ 搜索索引优化

### 安全性
- ✅ 速率限制
- ✅ SQL 注入防护（ORM）
- ✅ CORS 配置
- ✅ 输入验证

### 可扩展性
- ✅ 模块化设计
- ✅ 易于添加新的论文源
- ✅ 插件式爬虫架构
- ✅ Docker 容器化

### 可维护性
- ✅ 详细日志记录（loguru）
- ✅ 类型提示
- ✅ 清晰的代码结构
- ✅ 配置与代码分离

## 📝 配置说明

### 环境变量 (`.env`)

```bash
# 应用设置
DEBUG=True
HOST=0.0.0.0
PORT=8000

# 数据库（生产环境建议使用 PostgreSQL）
DATABASE_URL=sqlite+aiosqlite:///./coolpapers.db
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/coolpapers

# Redis 缓存（可选）
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=False

# ArXiv 设置
ARXIV_RATE_LIMIT=3.0

# PDF 处理
PDF_MAX_SIZE_MB=50

# 搜索引擎
SEARCH_MAX_RESULTS=1000

# API 密钥（如果需要）
KIMI_API_KEY=your_api_key_here
```

## 🧪 测试

```bash
# 运行测试
pytest tests/ -v

# 测试覆盖率
pytest --cov=. tests/
```

## 📚 API 文档

启动服务后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查 `DATABASE_URL` 配置
   - 确保数据库文件有写权限

2. **ArXiv 爬取失败**
   - 检查网络连接
   - 增加 `ARXIV_RATE_LIMIT` 值

3. **搜索索引问题**
   - 删除 `search_index/` 目录重建
   - 重启应用自动重建索引

4. **PDF 下载超时**
   - 增加 HTTP 超时时间
   - 检查 PDF URL 是否有效

## 🎯 与原 Cool Papers 的对比

| 功能 | 原项目（推测） | 本实现 | 状态 |
|------|--------------|--------|------|
| ArXiv 爬虫 | ✓ | ✓ | ✅ 完成 |
| OpenReview 爬虫 | ✓ | ✓ | ✅ 完成 |
| ACL/PMLR 爬虫 | ✓ | ✓ | ✅ 完成 |
| PDF 文本提取 | ✓ | ✓ | ✅ 完成 |
| BM25 搜索 | ✓ (tantivy) | ✓ (tantivy) | ✅ 完成 |
| RSS/Atom Feed | ✓ | ✓ | ✅ 完成 |
| 用户行为追踪 | ✓ | ✓ | ✅ 完成 |
| Kimi AI 摘要 | ✓ | 🔌 接口预留 | ⚠️ 需 API Key |
| 前端页面 | ✓ | ❌ | 📋 未实现 |

## 🚀 后续可以扩展的功能

1. **前端页面** - 使用 React/Vue 实现浏览界面
2. **用户系统** - 注册、登录、个人收藏
3. **推荐系统** - 基于用户行为的论文推荐
4. **AI 摘要集成** - 接入 Kimi 或其他 LLM API
5. **邮件订阅** - 定期发送论文更新
6. **论文关系图谱** - 引用关系可视化
7. **更多论文源** - bioRxiv, IJCAI, AAAI 等

## 📄 许可证

MIT License

## 🙏 致谢

本项目受 [Cool Papers](https://papers.cool) 启发，重新实现了其核心后端功能。

---

**项目已完成并可立即使用！** 🎉

如有问题或建议，欢迎提 Issue！
