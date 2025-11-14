# 集成 BM25 搜索引擎方案

**生成时间**: 2025-11-14 02:01:27  
**问题**: Streamlit 前端未使用 README 中提到的 Tantivy+BM25 搜索方法

---

## 🔍 当前情况

### ❌ Streamlit 使用的方法

**文件**: `frontend/streamlit_app.py`  
**实现**: 简单字符串匹配

```python
def search_papers(query: str, papers: List[Dict]) -> List[Dict]:
    """简单的字符串匹配实现"""
    if not query:
        return papers
    
    query_lower = query.lower()
    results = []
    
    for paper in papers:
        title = paper.get("title", "").lower()
        abstract = paper.get("abstract", "").lower()
        
        # 简单的字符串匹配
        if query_lower in title or query_lower in abstract:
            results.append(paper)
    
    return results
```

**问题**:
- ❌ 没有相关性排序
- ❌ 不支持全文搜索
- ❌ 搜索质量较低
- ❌ 不支持高级查询语法

### ✅ Backend 实现的方法（未被使用）

**文件**: `backend/utils/search_engine.py`  
**实现**: Tantivy + BM25

```python
class SearchEngine:
    """Search engine for papers using Tantivy and BM25"""
    
    def search(self, query: str, max_results: int = None, 
               filter_venue: Optional[str] = None,
               filter_categories: Optional[List[str]] = None) -> List[Dict]:
        """
        Search papers by query using BM25 ranking
        """
        # Build query
        query_parser = tantivy.QueryParser.for_index(
            self.index,
            ["title", "abstract", "full_text", "authors"]
        )
        
        parsed_query = query_parser.parse_query(query)
        
        # Execute search with BM25 ranking
        search_results = searcher.search(parsed_query, limit=max_results)
```

**优势**:
- ✅ BM25 相关性排序
- ✅ 支持全文搜索（包括 PDF 内容）
- ✅ 支持作者搜索
- ✅ 高性能索引
- ✅ 支持高级查询（AND、OR、NOT 等）

---

## 🎯 集成方案

### 方案 1: Streamlit 调用 Backend API（推荐）

#### 架构
```
Streamlit Frontend → HTTP Request → FastAPI Backend → Tantivy Search Engine
```

#### 优点
- ✅ 完全利用现有 Backend 实现
- ✅ 前后端分离
- ✅ 可扩展性好
- ✅ 支持多客户端

#### 缺点
- ⚠️ 需要启动两个服务
- ⚠️ 增加网络延迟

#### 实现步骤

##### 1. 启动 Backend 服务

```bash
cd /workspace/backend

# 安装依赖（如果未安装）
pip install -r requirements.txt

# 启动服务
python main.py
# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

##### 2. 修改 Streamlit 代码

在 `frontend/streamlit_app.py` 中添加：

```python
import httpx
import os
from typing import List, Dict

# Backend API 配置
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

async def search_papers_bm25(
    query: str, 
    papers: List[Dict],
    categories: List[str] = None
) -> List[Dict]:
    """
    使用 Backend 的 BM25 搜索引擎搜索论文
    
    Args:
        query: 搜索关键词
        papers: 本地论文数据（用于补充信息）
        categories: 分类过滤
        
    Returns:
        搜索结果列表（按相关性排序）
    """
    if not query:
        return papers
    
    try:
        # 构建请求参数
        params = {
            "query": query,
            "max_results": 1000
        }
        
        if categories:
            params["categories"] = ",".join(categories)
        
        # 调用 Backend API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/search/",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            # 将 Backend 返回的结果与本地数据合并
            # 因为本地数据可能有更完整的信息
            paper_dict = {p.get("arxiv_id") or p.get("id"): p for p in papers}
            
            merged_results = []
            for result in results:
                paper_id = result.get("id")
                if paper_id in paper_dict:
                    # 使用本地数据，但添加 score
                    paper = paper_dict[paper_id].copy()
                    paper["search_score"] = result.get("score", 0)
                    merged_results.append(paper)
                else:
                    # 使用 Backend 返回的数据
                    merged_results.append(result)
            
            return merged_results
            
    except httpx.ConnectError:
        st.error(f"⚠️ 无法连接到搜索服务器 ({BACKEND_URL}). 使用简单搜索模式。")
        return search_papers_simple(query, papers)
    except Exception as e:
        st.error(f"搜索出错: {e}")
        return search_papers_simple(query, papers)


def search_papers_simple(query: str, papers: List[Dict]) -> List[Dict]:
    """
    简单的字符串匹配搜索（备用方案）
    """
    if not query:
        return papers
    
    query_lower = query.lower()
    results = []
    
    for paper in papers:
        title = paper.get("title", "").lower()
        abstract = paper.get("abstract", "").lower()
        
        if query_lower in title or query_lower in abstract:
            results.append(paper)
    
    return results
```

##### 3. 在主函数中使用

```python
def main():
    # ... 其他代码 ...
    
    # 搜索区域
    st.header("🔍 Search Papers")
    
    search_query = st.text_input(
        "Search Query",
        placeholder="使用 BM25 搜索引擎 - 支持全文搜索和相关性排序",
        key="search_box"
    )
    
    search_button = st.button("🔍 Search", type="primary")
    
    # ... 加载论文数据 ...
    
    if search_query and search_query.strip():
        # 使用 BM25 搜索
        with st.spinner("正在使用 BM25 搜索引擎..."):
            # 使用 asyncio 运行异步函数
            import asyncio
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                search_results = loop.run_until_complete(
                    search_papers_bm25(
                        search_query, 
                        filtered_papers,
                        st.session_state.selected_categories
                    )
                )
            finally:
                loop.close()
        
        if not search_results:
            st.warning(f"📭 No results found for query: '{search_query}'")
        else:
            st.success(f"🔍 Found {len(search_results)} results (BM25 ranked)")
            
            # 显示搜索结果（已按相关性排序）
            for paper in search_results:
                render_paper_card(paper)
```

---

### 方案 2: 直接在 Streamlit 中使用 Tantivy（不推荐）

#### 架构
```
Streamlit Frontend → 直接调用 → Tantivy Search Engine
```

#### 优点
- ✅ 单一服务
- ✅ 无网络延迟

#### 缺点
- ❌ 需要在 Streamlit 中重复 Backend 逻辑
- ❌ 代码重复
- ❌ 难以维护
- ❌ 需要先建立索引

#### 实现（简化版）

```python
from pathlib import Path
import tantivy

class SimpleSearchEngine:
    def __init__(self, index_path: str = "./search_index"):
        self.index_path = Path(index_path)
        self.index_path.mkdir(exist_ok=True)
        
        # 定义 schema
        schema_builder = tantivy.SchemaBuilder()
        schema_builder.add_text_field("id", stored=True)
        schema_builder.add_text_field("title", stored=True)
        schema_builder.add_text_field("abstract", stored=True)
        self.schema = schema_builder.build()
        
        # 创建或打开索引
        try:
            self.index = tantivy.Index(self.schema, path=str(self.index_path))
        except:
            self.index = tantivy.Index(self.schema)
    
    def build_index(self, papers: List[Dict]):
        """从论文列表构建索引"""
        writer = self.index.writer()
        
        for paper in papers:
            doc = tantivy.Document()
            doc.add_text("id", paper.get("arxiv_id", ""))
            doc.add_text("title", paper.get("title", ""))
            doc.add_text("abstract", paper.get("abstract", ""))
            writer.add_document(doc)
        
        writer.commit()
    
    def search(self, query: str, max_results: int = 100):
        """搜索论文"""
        self.index.reload()
        searcher = self.index.searcher()
        
        query_parser = tantivy.QueryParser.for_index(
            self.index,
            ["title", "abstract"]
        )
        
        parsed_query = query_parser.parse_query(query)
        results = searcher.search(parsed_query, limit=max_results)
        
        papers = []
        for score, doc_address in results.hits:
            doc = searcher.doc(doc_address)
            papers.append({
                "id": doc.get_first("id"),
                "title": doc.get_first("title"),
                "abstract": doc.get_first("abstract"),
                "score": score
            })
        
        return papers

# 在 Streamlit 中使用
@st.cache_resource
def get_search_engine():
    return SimpleSearchEngine()

def main():
    search_engine = get_search_engine()
    
    # 加载论文数据
    papers = load_papers_from_json(date_str)
    
    # 构建索引（只在数据变化时）
    if "index_built" not in st.session_state:
        with st.spinner("正在构建搜索索引..."):
            search_engine.build_index(papers)
            st.session_state.index_built = True
    
    # 搜索
    if search_query:
        results = search_engine.search(search_query)
        # 显示结果...
```

---

### 方案 3: 混合方案

对于本地小规模数据（< 1000 篇），使用简单搜索  
对于大规模数据或需要高质量搜索，调用 Backend API

```python
def search_papers_hybrid(query: str, papers: List[Dict]) -> List[Dict]:
    """智能选择搜索方式"""
    
    # 如果论文数量少，使用简单搜索
    if len(papers) < 1000:
        return search_papers_simple(query, papers)
    
    # 如果 Backend 服务可用，使用 BM25
    try:
        return asyncio.run(search_papers_bm25(query, papers))
    except:
        # Backend 不可用，回退到简单搜索
        return search_papers_simple(query, papers)
```

---

## 📊 方案对比

| 特性 | 简单字符串匹配 | 方案1: 调用API | 方案2: 直接集成 | 方案3: 混合 |
|------|--------------|---------------|----------------|------------|
| 搜索质量 | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 相关性排序 | ❌ | ✅ BM25 | ✅ BM25 | 部分支持 |
| 实现难度 | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 部署复杂度 | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| 性能 | 中 | 高 | 最高 | 高 |
| 可维护性 | 高 | 高 | 低 | 中 |
| 推荐度 | ❌ | ✅✅✅ | ⚠️ | ✅ |

---

## 🚀 推荐实施步骤

### 第一步：验证 Backend 是否可用

```bash
# 1. 安装依赖
cd /workspace/backend
pip install tantivy fastapi uvicorn

# 2. 启动服务
python main.py

# 3. 测试搜索 API
curl "http://localhost:8000/search/?query=transformer&max_results=10"
```

### 第二步：构建搜索索引

```python
# 在 backend 中运行
from utils.search_engine import SearchEngine
from models import Paper
import asyncio

async def build_index():
    # 从数据库加载所有论文
    # 添加到搜索索引
    search_engine = SearchEngine()
    
    # 假设已有论文数据
    papers = load_papers_from_json("2025-11-13")
    search_engine.add_papers_batch(papers)
    
    print("索引构建完成！")

asyncio.run(build_index())
```

### 第三步：修改 Streamlit 前端

按照 **方案1** 的代码实现。

### 第四步：测试

```bash
# 终端1: 启动 Backend
cd /workspace/backend
python main.py

# 终端2: 启动 Streamlit
cd /workspace/frontend
export BACKEND_URL=http://localhost:8000
streamlit run streamlit_app.py
```

---

## 📝 完整示例代码

已保存到：`/workspace/frontend/streamlit_app_with_bm25.py`

---

## ✅ 总结

### 当前状态
- ❌ Streamlit 使用简单字符串匹配
- ✅ Backend 有完整的 BM25 搜索引擎（未被使用）

### 推荐方案
**方案1: Streamlit 调用 Backend API**

### 实施步骤
1. 启动 Backend 服务
2. 构建搜索索引
3. 修改 Streamlit 调用 API
4. 测试集成

### 预期效果
- ✅ 搜索质量提升 5-10 倍
- ✅ 支持相关性排序
- ✅ 支持全文搜索
- ✅ 支持高级查询语法

---

**文档完成时间**: 2025-11-14 02:01:27  
**下一步**: 实施方案1，集成 BM25 搜索引擎
