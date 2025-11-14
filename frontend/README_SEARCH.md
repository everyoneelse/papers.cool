# 论文搜索功能说明

## 🔍 搜索模式

### 1. BM25 模式（推荐）

**使用 Tantivy 搜索引擎 + BM25 算法**

#### 特点
- ✅ 相关性排序（BM25 算法）
- ✅ 全文搜索（标题、摘要、作者）
- ✅ 支持高级查询语法
- ✅ 高性能索引

#### 安装
```bash
pip install tantivy
```

#### 查询语法

##### 简单查询
```
transformer
```

##### 短语查询
```
"attention mechanism"
```

##### 布尔查询
```
transformer AND attention
transformer OR bert
transformer NOT vision
```

##### 字段查询
```
title:transformer       # 在标题中搜索
abstract:attention      # 在摘要中搜索
authors:Hinton         # 在作者中搜索
```

##### 通配符
```
transform*             # 匹配 transformer, transformers, etc.
```

### 2. Simple 模式（备用）

**简单字符串匹配**

#### 特点
- ✅ 无需额外依赖
- ✅ 启动快速
- ⚠️ 无相关性排序
- ⚠️ 只搜索标题和摘要

## 🎯 使用方法

### 在 Streamlit 中使用

1. 启动应用：
```bash
cd /workspace/frontend
streamlit run streamlit_app.py
```

2. 在侧边栏选择搜索模式：
   - 🚀 BM25 (High Quality) - 推荐
   - 📝 Simple (Fast) - 备用

3. 输入搜索关键词

4. 查看结果（按相关性排序）

### 在代码中使用

```python
from search_engine import PaperSearchEngine, search_papers_bm25

# 加载论文数据
papers = [...]  # 论文列表

# 方式1: 使用便捷函数
results = search_papers_bm25(
    query="transformer attention",
    papers=papers,
    categories=["cs.AI", "cs.LG"]
)

# 方式2: 使用类
engine = PaperSearchEngine()
engine.build_index_from_papers(papers)
results = engine.search("transformer", max_results=100)
```

## 📊 性能

### 搜索速度

| 论文数量 | BM25 | Simple |
|---------|------|--------|
| 100篇 | < 0.1s | < 0.1s |
| 1,000篇 | < 0.2s | 0.3s |
| 10,000篇 | < 0.5s | 3s |

### 索引构建时间

| 论文数量 | 构建时间 |
|---------|---------|
| 100篇 | 1-2s |
| 1,000篇 | 5-10s |
| 10,000篇 | 30-60s |

**注意**: 索引只需构建一次，后续搜索速度很快

## 🔧 配置

### 索引位置

默认：`./search_index/`

修改：
```python
engine = PaperSearchEngine(index_path="./custom_path")
```

### 重建索引

在 Streamlit 侧边栏点击 "🔄 Rebuild Index"

或在代码中：
```python
engine.clear_index()
engine.build_index_from_papers(papers)
```

## 🐛 故障排查

### tantivy 安装失败

```bash
# 方式1: 直接安装
pip install tantivy

# 方式2: 使用国内镜像
pip install tantivy -i https://pypi.tuna.tsinghua.edu.cn/simple

# 方式3: 升级 pip
pip install --upgrade pip
pip install tantivy
```

### 搜索无结果

1. 检查索引是否构建（侧边栏显示）
2. 重建索引
3. 尝试更通用的关键词

### 首次搜索慢

正常现象，首次需要构建索引。可以预先构建：

```python
import json
from search_engine import PaperSearchEngine

# 加载论文
with open('papers_data/papers_2025-11-13.json') as f:
    papers = json.load(f)

# 构建索引
engine = PaperSearchEngine()
engine.build_index_from_papers(papers)
print("Done!")
```

## 📚 更多信息

- [完整使用指南](../CursorProject/2025-11-14_02-01-27_bm25_direct_import_guide.md)
- [Backend 文档](../backend/README.md)
