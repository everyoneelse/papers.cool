"""
TEST PAGE
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional
import json
import os
from pathlib import Path
import io

import sys
sys.path.append("/home/hhy/project/paper-agent/papers.cool-main/backend/utils")
# 导入 BM25 搜索引擎
try:
    from search_engine import PaperSearchEngine, search_papers_bm25
    SEARCH_ENGINE_AVAILABLE = True
except ImportError:
    SEARCH_ENGINE_AVAILABLE = False
    st.warning("⚠️ Tantivy 搜索引擎不可用，将使用简单搜索模式。请安装: pip install tantivy")


# 页面配置
st.set_page_config(
    page_title="TEST PAGE",
    page_icon="📝",
)

# 数据目录 - 假设论文数据按日期存储为JSON文件
DATA_DIR = os.getenv("DATA_DIR", "/home/hhy/project/paper-agent/papers-agent/papers_data")
#DATA_DIR = os.getenv("DATA_DIR", "./papers_data")

# 后端 API 地址
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

# 初始化 session state
if "starred_papers" not in st.session_state:
    st.session_state.starred_papers = set()
if "viewed_papers" not in st.session_state:
    st.session_state.viewed_papers = set()
if "selected_categories" not in st.session_state:
    st.session_state.selected_categories = ["cs.AI", "cs.CL", "cs.LG"]

if "search_engine" not in st.session_state and SEARCH_ENGINE_AVAILABLE:
    st.session_state.search_engine = None

if "search_mode" not in st.session_state:
    st.session_state.search_mode = "bm25" if SEARCH_ENGINE_AVAILABLE else "simple"


# ArXiv 分类定义
ARXIV_CATEGORIES = {
    "Artificial Intelligence (cs.AI)": "cs.AI",
    "Computation and Language (cs.CL)": "cs.CL",
    "Computer Vision (cs.CV)": "cs.CV",
    "Machine Learning (cs.LG)": "cs.LG",
    "Neural and Evolutionary Computing (cs.NE)": "cs.NE",
    "Computational Complexity (cs.CC)": "cs.CC",
    "Statistics - Machine Learning (stat.ML)": "stat.ML",
}

# Pills 胶囊式颜色定义 - 使用柔和的配色方案
CATEGORY_COLORS = {
    "cs.AI": {"bg": "#FFE5E5", "border": "#FF6B6B", "text": "#CC0000"},           # 柔和红
    "cs.CL": {"bg": "#E0F7F7", "border": "#4ECDC4", "text": "#008B8B"},           # 柔和青
    "cs.CV": {"bg": "#E3F2FD", "border": "#45B7D1", "text": "#1565C0"},           # 柔和蓝
    "cs.LG": {"bg": "#E8F5E9", "border": "#96CEB4", "text": "#2E7D32"},           # 柔和绿
    "cs.NE": {"bg": "#FFF9E6", "border": "#FFEAA7", "text": "#F57F17"},           # 柔和黄
    "cs.CC": {"bg": "#F5F5F5", "border": "#DFE6E9", "text": "#616161"},           # 柔和灰
    "stat.ML": {"bg": "#F3E5F5", "border": "#A29BFE", "text": "#6A1B9A"},         # 柔和紫
}


def load_papers_from_json(date_str: str, selected_categories: List[str] = None) -> List[Dict]:
    """
    从JSON文件加载指定日期的论文数据
    支持新的按类别组织格式和旧的总文件格式:
    1. 新格式: papers_data/cs.AI/papers_YYYY-MM-DD_100percent.json (按类别文件夹)
    2. 旧格式: papers_data/papers_YYYY-MM-DD_100percent.json (总文件)
    """
    data_path = Path(DATA_DIR)
    all_papers = []

    # 首先尝试新的按类别组织格式
    category_files_found = False

    # 确定要加载的类别
    categories_to_load = selected_categories if selected_categories else ARXIV_CATEGORIES.values()

    for category in categories_to_load:
        category_dir = data_path / category
        json_file = category_dir / f"papers_{date_str}_100percent.json"

        if json_file.exists():
            category_files_found = True
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 处理数据格式
                    if isinstance(data, dict) and "papers" in data:
                        papers = data["papers"]
                        all_papers.extend(papers)
                    else:
                        continue

            except Exception as e:
                continue

    # 如果找到了类别文件，直接返回合并的结果
    if category_files_found and all_papers:
        # 去重（按 arxiv_id）
        unique_papers = {}
        for paper in all_papers:
            arxiv_id = paper.get("arxiv_id", paper.get("id", ""))
            if arxiv_id and arxiv_id not in unique_papers:
                unique_papers[arxiv_id] = paper

        result_papers = list(unique_papers.values())
        return result_papers

    # 如果没有找到类别文件，尝试旧的总文件格式
    legacy_files = [
        data_path / f"papers_{date_str}_100percent.json",
        data_path / f"papers_{date_str}.json",
    ]

    for json_file in legacy_files:
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 处理不同的数据格式
                    if isinstance(data, list):
                        # 直接是论文列表
                        all_papers = data
                    elif isinstance(data, dict):
                        # 包含 metadata 的格式
                        if "papers" in data:
                            all_papers = data["papers"]
                        else:
                            # 可能是单个论文对象，转换为列表
                            all_papers = [data]
                    else:
                        st.warning(f"Unexpected data format in {json_file}")
                        continue
                        
                    st.success(f"✅ Loaded {len(all_papers)} papers from legacy file {json_file}")
                    return all_papers

            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON in {json_file}: {e}")
                continue
            except Exception as e:
                st.error(f"Error loading papers from {json_file}: {e}")
                continue
    
    # 没有找到任何文件
    return []


def filter_papers_by_categories(papers: List[Dict], categories: List[str]) -> List[Dict]:
    """根据选择的分类过滤论文"""
    if not categories:
        return papers
    
    # 转换分类名称为代码
    category_codes = [ARXIV_CATEGORIES.get(cat, cat) for cat in categories]
    
    filtered = []
    for paper in papers:
        paper_categories = paper.get("categories", [])
        if isinstance(paper_categories, str):
            paper_categories = [paper_categories]
        
        # 检查论文是否属于任一选中的分类
        if any(cat in paper_categories for cat in category_codes):
            filtered.append(paper)
    
    return filtered


def search_papers_simple(query: str, papers: List[Dict], categories: Optional[List[str]] = None) -> List[Dict]:
    """
    在论文中搜索（搜索标题和摘要）
    简单的字符串匹配实现

    Args:
        query: 搜索关键词
        papers: 论文列表
        categories: 分类过滤列表

    Returns:
        搜索结果列表
    """
    if not query:
        return papers

    query_lower = query.lower()
    results = []

    for paper in papers:
        title = paper.get("title", "").lower()
        abstract = paper.get("abstract", "").lower()

        # 简单的字符串匹配
        if query_lower in title or query_lower in abstract:
            # 应用分类过滤（如果指定了分类）
            if categories:
                paper_categories = paper.get("categories", [])
                if isinstance(paper_categories, str):
                    paper_categories = [paper_categories]

                if not any(cat in paper_categories for cat in categories):
                    continue

            results.append(paper)

    return results


def search_papers(query: str, papers: List[Dict], categories: Optional[List[str]] = None) -> List[Dict]:
    """
    搜索论文 - 智能选择搜索方式
    
    Args:
        query: 搜索关键词
        papers: 论文列表
        categories: 分类过滤
        
    Returns:
        搜索结果列表
    """
    if not query or not query.strip():
        return papers
    
    # 如果 BM25 搜索引擎可用，优先使用
    if SEARCH_ENGINE_AVAILABLE and st.session_state.search_mode == "bm25":
        try:
            # 初始化或获取搜索引擎
            if st.session_state.search_engine is None:
                st.session_state.search_engine = PaperSearchEngine()
            
            # 使用 BM25 搜索
            results = search_papers_bm25(
                query=query,
                papers=papers,
                categories=categories,
                search_engine=st.session_state.search_engine,
                rebuild_index=True  # 每次都重建索引，确保只搜索当前论文
            )
            
            return results
            
        except Exception as e:
            st.warning(f"⚠️ BM25 搜索失败，使用简单搜索: {e}")
            return search_papers_simple(query, papers, categories)
    else:
        # 使用简单搜索
        return search_papers_simple(query, papers, categories)


def render_category_pills(categories: List[str]):
    """渲染 Pills 胶囊式分类标签 - 使用Streamlit原生组件"""

    # 创建胶囊HTML
    pills_html = ""
    for cat in categories:
        colors = CATEGORY_COLORS.get(cat, {"bg": "#F0F0F0", "border": "#BDBDBD", "text": "#424242"})
        pills_html += f'<span style="background-color:{colors["bg"]};color:{colors["text"]};border:2px solid {colors["border"]};padding:6px 12px;border-radius:15px;font-size:12px;font-weight:500;margin:0 4px 4px 0;display:inline-block;">🔖 {cat}</span>'

    st.markdown(f'<div style="margin:10px 0;">{pills_html}</div>', unsafe_allow_html=True)

def papers_to_csv(papers: List[Dict]) -> str:
    """
    将论文列表转换为CSV字符串

    Args:
        papers: 论文列表

    Returns:
        CSV格式的字符串
    """
    if not papers:
        return ""

    # 定义CSV列
    columns = ['title', 'authors', 'categories', 'published_date', 'abstract', 'url', 'pdf_url']

    # 创建数据行
    data = []
    for paper in papers:
        row = {
            'title': paper.get('title', ''),
            'authors': ', '.join(paper.get('authors', [])) if isinstance(paper.get('authors'), list) else paper.get('authors', ''),
            'categories': ', '.join(paper.get('categories', [])) if isinstance(paper.get('categories'), list) else paper.get('categories', ''),
            'published_date': paper.get('published_date', ''),
            'abstract': paper.get('abstract', ''),
            'url': paper.get('url', ''),
            'pdf_url': paper.get('pdf_url', '')
        }
        data.append(row)

    # 转换为DataFrame然后导出为CSV
    df = pd.DataFrame(data, columns=columns)
    return df.to_csv(index=False)


def render_paper_card(paper: Dict):

    """渲染单个论文卡片"""

    # 论文容器
    with st.container():
        # 标题
        title = paper.get("title", "Untitled")
        url = paper.get("url", "") or paper.get("pdf_url", "")
        
        if url:
            st.markdown(f"### [{title}]({url})")
        else:
            st.markdown(f"### {title}")

        # 作者
        authors = paper.get("authors", [])
        if authors:
            if isinstance(authors, list):
                if len(authors) > 5:
                    author_str = ", ".join(authors[:5]) + " et al."
                else:
                    author_str = ", ".join(authors)
            else:
                author_str = str(authors)
            st.markdown(f"**👥 Authors:** {author_str}")
        
        # 分类和发布日期
        col1, col2 = st.columns(2)
        with col1:
            categories = paper.get("categories", [])
            if categories:
                if isinstance(categories, list):
                    categories_str = ", ".join(categories[:3])
                else:
                    categories_str = str(categories)
                st.caption(f"🏷️ Categories: {categories_str}")        
        with col2:
            pub_date = paper.get("published_date")
            if pub_date:
                st.caption(f"📅 Published: {pub_date}")
        
        # 摘要
        abstract = paper.get("abstract", "")
        if abstract:
            st.markdown("#### 📄 Abstract")
            st.write(abstract)

        # 链接按钮
        col1, _ = st.columns([1, 4])
        
        with col1:
            pdf_url = paper.get("pdf_url", "")
            if pdf_url:
                st.link_button("📄 PDF", pdf_url)
        
             
        # 分割线
        st.divider()



        # 分割线
        st.divider()

def main():
    """主应用"""
    
    # 自定义 CSS
    st.markdown("""
    <style>
    div[data-testid="stExpander"] {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 侧边栏 - ArXiv 分类选择
    with st.sidebar:
        st.title("📚 Cool Papers")
        st.caption("Simplified Interface")
        
        st.markdown("---")
        
        # ArXiv 分类选择
        st.subheader("🔬 arXiv Categories")
        st.caption("Select your interested categories")
        
        selected_cats = []
        for cat_name, cat_code in ARXIV_CATEGORIES.items():
            is_selected = cat_code in st.session_state.selected_categories
            if st.checkbox(cat_name, value=is_selected, key=f"cat_{cat_code}"):
                selected_cats.append(cat_code)
        
        st.session_state.selected_categories = selected_cats
        
        st.markdown("---")
        
        # 显示选中的分类数量
        st.metric("📂 Selected Categories", len(st.session_state.selected_categories))
        
        st.markdown("---")
        
        # 关于
        st.caption("**About**")
        st.caption("Cool Papers - Simplified Interface")
        st.caption("Data loaded from local JSON files")
    
    # 主页面
    st.header("arxiv 论文同步")

    st.markdown("---")

    # 日期和分类并排显示
    date_col, cat_col = st.columns([1, 3])

    with date_col:
        st.caption("选择日期")
        selected_date = st.date_input(
            "Select a date to view papers",
            value=datetime.now(),
            max_value=datetime.now(),
            min_value=datetime.now() - timedelta(days=365),
            key="date_picker",
            label_visibility="collapsed"
        )

    with cat_col:
        st.caption("类别")
        if st.session_state.selected_categories:
            render_category_pills(st.session_state.selected_categories)
        else:
            st.warning("⚠️ Please select at least one category from the sidebar")

    date_str = selected_date.strftime("%Y-%m-%d")

    st.markdown("---")

    # 搜索区域 - 单独一行
    st.header("搜索")

    search_col1, search_col2, export_col = st.columns([4, 1, 1])
    with search_col1:
        search_query = st.text_input(
            "Search Query",
            placeholder="输入关键词 或者 什么都不输入",
            label_visibility="collapsed",
            key="search_box"
        )

    with search_col2:
        search_button = st.button("Search", type="primary", use_container_width=True)

    # 导出按钮会在这里动态添加（当有论文时）
    
    st.markdown("---")
    
    # 加载并显示论文
    if st.session_state.selected_categories:
        with st.spinner(f"Loading papers for {date_str}..."):
            # 加载论文
            papers = load_papers_from_json(date_str, st.session_state.selected_categories)

            if not papers:
                st.warning(f"📭 No papers found for date {date_str}")
            else:
                # 论文已经按选中的类别加载，无需额外过滤
                # 确定要显示的论文列表
                if search_query and search_query.strip():
                    # 在加载的论文中搜索
                    display_papers = search_papers(search_query, papers, st.session_state.selected_categories)

                    if not display_papers:
                        st.info(f"No results found for '{search_query}'")
                    else:
                        st.success(f"Found {len(display_papers)} papers matching '{search_query}'")
                else:
                    # 显示总加载论文数量
                    st.success(f"✅ Loaded {len(papers)} papers")
                    display_papers = papers

                # 在搜索区域添加导出按钮
                if display_papers:
                    with export_col:
                        csv_data = papers_to_csv(display_papers)
                        # 使用稳定的key，避免媒体文件缓存冲突
                        download_key = f"download_csv_{date_str}"
                        st.download_button(
                            label="Export CSV",
                            data=csv_data,
                            file_name=f"papers_{date_str}.csv",
                            mime="text/csv",
                            key=download_key,
                            use_container_width=True
                        )

                # 显示论文列表
                for paper in display_papers:
                    render_paper_card(paper)
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p><strong>Cool Papers</strong> - Simplified Streamlit Interface</p>
        <p>Data loaded from local JSON files</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
