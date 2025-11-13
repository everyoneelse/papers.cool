"""
Cool Papers - Simplified Streamlit Frontend
简化的Streamlit前端 - 单页面论文浏览和搜索
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional
import json
import os
from pathlib import Path

# 页面配置
st.set_page_config(
    page_title="Cool Papers",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据目录 - 假设论文数据按日期存储为JSON文件
DATA_DIR = os.getenv("DATA_DIR", "./papers_data")

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

# 初始化 session state
if "selected_categories" not in st.session_state:
    st.session_state.selected_categories = ["cs.AI", "cs.LG"]


def load_papers_from_json(date_str: str) -> List[Dict]:
    """
    从JSON文件加载指定日期的论文数据
    假设文件命名格式为: papers_YYYY-MM-DD.json
    """
    data_path = Path(DATA_DIR)
    json_file = data_path / f"papers_{date_str}.json"
    
    if not json_file.exists():
        return []
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
            return papers if isinstance(papers, list) else []
    except Exception as e:
        st.error(f"Error loading papers from {json_file}: {e}")
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


def search_papers(query: str, papers: List[Dict]) -> List[Dict]:
    """
    在论文中搜索（搜索标题和摘要）
    简单的字符串匹配实现
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
            results.append(paper)
    
    return results


def render_category_pills(categories: List[str]):
    """渲染 Pills 胶囊式分类标签"""
    pills_html = '<div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0;">'
    
    # 默认颜色（灰色系）
    default_colors = {"bg": "#F0F0F0", "border": "#BDBDBD", "text": "#424242"}
    
    for cat in categories:
        colors = CATEGORY_COLORS.get(cat, default_colors)
        pills_html += f'''
            <span style="
                background-color: {colors['bg']}; 
                color: {colors['text']}; 
                border: 2px solid {colors['border']};
                padding: 8px 20px; 
                border-radius: 25px; 
                font-size: 15px; 
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                transition: all 0.3s ease;
                cursor: default;
            "
            onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)';"
            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.08)';"
            >
                <span style="font-size: 18px;">🔖</span>
                <span>{cat}</span>
            </span>
        '''
    
    pills_html += '</div>'
    return pills_html


def render_paper_card(paper: Dict):
    """渲染单个论文卡片"""
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
            st.caption(f"👥 {author_str}")
        
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
            with st.expander("📄 Abstract", expanded=False):
                st.write(abstract)
        
        # 链接按钮
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            pdf_url = paper.get("pdf_url", "")
            if pdf_url:
                st.link_button("📄 PDF", pdf_url)
        
        with col2:
            if url:
                st.link_button("🔗 Link", url)
        
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
    st.title("📚 Cool Papers - Paper Browser & Search")
    st.subheader("Browse arXiv papers by category and date, or search within a specific date")
    
    st.markdown("---")
    
    # 显示当前选择的分类 - 使用 Pills 胶囊式标签
    if st.session_state.selected_categories:
        st.markdown("### 🔬 Current Selected Categories")
        pills_html = render_category_pills(st.session_state.selected_categories)
        st.markdown(pills_html, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Please select at least one category from the sidebar")
    
    # 日期选择 - 使用弹窗式日期选择器
    st.header("📅 Select Date")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_date = st.date_input(
            "Select a date to view papers",
            value=datetime.now(),
            max_value=datetime.now(),
            min_value=datetime.now() - timedelta(days=365),
            key="date_picker"
        )
    
    date_str = selected_date.strftime("%Y-%m-%d")
    
    st.markdown("---")
    
    # 搜索区域
    st.header("🔍 Search Papers")
    
    col1, col2 = st.columns([5, 1])
    with col1:
        search_query = st.text_input(
            "Search Query",
            placeholder="Enter keywords to search in titles and abstracts (or leave empty to show all papers)",
            label_visibility="collapsed",
            key="search_box"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # 加载并显示论文
    if st.session_state.selected_categories:
        with st.spinner(f"Loading papers for {date_str}..."):
            # 加载论文
            papers = load_papers_from_json(date_str)
            
            if not papers:
                st.warning(f"📭 No papers found for date {date_str}")
            else:
                # 根据分类过滤
                filtered_papers = filter_papers_by_categories(
                    papers, 
                    st.session_state.selected_categories
                )
                
                if not filtered_papers:
                    st.warning(f"📭 No papers found in selected categories for {date_str}")
                else:
                    # 如果有搜索查询，则进行搜索
                    if search_query and search_query.strip():
                        search_results = search_papers(search_query, filtered_papers)
                        
                        if not search_results:
                            st.warning(f"📭 No results found for query: '{search_query}'")
                        else:
                            st.success(f"🔍 Found {len(search_results)} results for '{search_query}' in {date_str}")
                            
                            # 显示搜索结果
                            for paper in search_results:
                                render_paper_card(paper)
                    else:
                        # 没有搜索查询，显示所有论文
                        st.success(f"✅ Found {len(filtered_papers)} papers for {date_str}")
                        
                        # 显示论文列表
                        for paper in filtered_papers:
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
