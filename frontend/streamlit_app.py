"""
Cool Papers - Streamlit Frontend
沉浸式刷论文！Immersive Paper Discovery
"""

import streamlit as st
from datetime import datetime, timedelta
import httpx
from typing import List, Dict, Optional
import json
from urllib.parse import quote

# 页面配置 - 去掉侧边栏
st.set_page_config(
    page_title="Cool Papers - Immersive Paper Discovery",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"  # 隐藏侧边栏
)

# 后端 API 地址
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

# 初始化 session state
if "starred_papers" not in st.session_state:
    st.session_state.starred_papers = set()
if "viewed_papers" not in st.session_state:
    st.session_state.viewed_papers = set()
if "selected_categories" not in st.session_state:
    st.session_state.selected_categories = ["cs.AI", "cs.CL", "cs.LG"]


# ArXiv 分类定义
ARXIV_CATEGORIES = {
    "Artificial Intelligence (cs.AI)": ["cs.AI", "Computer Science - Artificial Intelligence"],
    "Computation and Language (cs.CL)": ["cs.CL", "Computer Science - Computation and Language"],
    "Computer Vision (cs.CV)": ["cs.CV", "Computer Science - Computer Vision and Pattern Recognition"],
    "Machine Learning (cs.LG)": ["cs.LG", "Computer Science - Machine Learning"],
    "Neural and Evolutionary Computing (cs.NE)": ["cs.NE", "Computer Science - Neural and Evolutionary Computing"],
    "Computational Complexity (cs.CC)": ["cs.CC", "Computer Science - Computational Complexity"],
    "Statistics - Machine Learning (stat.ML)": ["stat.ML", "Statistics - Machine Learning"],
}



def api_get(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """调用后端 API"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_BASE_URL}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        st.error(f"API 错误: {str(e)}")
        return None


def render_paper_card(paper: Dict, show_pdf: bool = False, show_kimi: bool = False):
    """渲染单个论文卡片"""
    paper_id = paper.get("id", "")
    is_starred = paper_id in st.session_state.starred_papers
    is_viewed = paper_id in st.session_state.viewed_papers
    
    # 论文容器
    with st.container():
        # 标题行
        col1, col2 = st.columns([10, 1])
        
        with col1:
            # 论文 ID 和标题
            title_prefix = f"**#{paper_id.split('@')[0] if '@' in paper_id else paper_id}** " if paper_id else ""
            st.markdown(f"{title_prefix}{paper.get('title', 'Untitled')}")
        
        with col2:
            # 星标按钮
            star_icon = "⭐" if is_starred else "☆"
            if st.button(star_icon, key=f"star_{paper_id}", help="Star this paper"):
                if is_starred:
                    st.session_state.starred_papers.discard(paper_id)
                else:
                    st.session_state.starred_papers.add(paper_id)
                st.rerun()
        
        # 作者
        authors = paper.get("authors", [])
        if authors:
            if len(authors) > 5:
                author_str = ", ".join(authors[:5]) + " et al."
            else:
                author_str = ", ".join(authors)
            st.caption(f"👥 {author_str}")
        
        # 分类和发布日期
        col1, col2 = st.columns(2)
        with col1:
            categories = paper.get("categories", [])
            if categories:
                st.caption(f"🏷️ Categories: {', '.join(categories[:3])}")
        
        with col2:
            pub_date = paper.get("published_date")
            if pub_date:
                st.caption(f"📅 Published: {pub_date}")
        
        # 摘要
        abstract = paper.get("abstract", "")
        if abstract:
            with st.expander("📄 Abstract", expanded=False):
                st.write(abstract)
        
        # 操作按钮
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
        
        with col1:
            pdf_url = paper.get("pdf_url", "")
            if pdf_url:
                if st.button("📄 PDF", key=f"pdf_{paper_id}", type="secondary"):
                    st.session_state.viewed_papers.add(paper_id)
                    show_pdf = True
        
        with col2:
            if st.button("🤖 Kimi", key=f"kimi_{paper_id}", type="secondary"):
                st.session_state.viewed_papers.add(paper_id)
                show_kimi = True
        
        with col3:
            paper_url = paper.get("url", "")
            if paper_url:
                st.link_button("🔗 Link", paper_url)
        
        # PDF 查看器
        if show_pdf and pdf_url:
            with st.expander("📄 PDF Viewer", expanded=True):
                st.markdown(f'<iframe src="{pdf_url}" width="100%" height="800px"></iframe>', 
                          unsafe_allow_html=True)
        
        # Kimi 摘要
        if show_kimi:
            with st.expander("🤖 Kimi Summary", expanded=True):
                with st.spinner("Generating summary..."):
                    # TODO: 调用 Kimi API
                    st.info("Kimi summary feature coming soon! Please integrate with Kimi API.")
        
        # 分割线
        st.divider()


def main():
    """主应用 - 单页面设计"""
    
    # 自定义 CSS
    st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    /* 隐藏侧边栏切换按钮 */
    [data-testid="collapsedControl"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 应用标题
    st.title("📚 Immersive Paper Discovery（沉浸式刷论文！）")
    
    st.markdown("---")
    
    # arXiv 分类选择 - 放在页面顶部
    st.header("🔬 arXiv Categories")
    st.caption("Select your interested categories")
    
    # 使用多列布局显示分类复选框
    cols = st.columns(4)
    selected_cats = []
    
    for idx, (cat_name, cat_info) in enumerate(ARXIV_CATEGORIES.items()):
        cat_id = cat_info[0]
        is_selected = cat_id in st.session_state.selected_categories
        
        with cols[idx % 4]:
            if st.checkbox(cat_name, value=is_selected, key=f"cat_{cat_id}"):
                selected_cats.append(cat_id)
    
    st.session_state.selected_categories = selected_cats
    
    # 统计信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⭐ Starred Papers", len(st.session_state.starred_papers))
    with col2:
        st.metric("👀 Viewed Papers", len(st.session_state.viewed_papers))
    with col3:
        st.metric("📂 Selected Categories", len(st.session_state.selected_categories))
    
    st.markdown("---")
    
    # 创建两个标签页：按日期浏览 和 搜索
    tab1, tab2 = st.tabs(["📅 Browse by Date", "🔍 Search Papers"])
    
    # 标签页 1: 按日期浏览 arXiv 论文
    with tab1:
        st.subheader("Browse arXiv Papers by Date")
        
        if not st.session_state.selected_categories:
            st.warning("⚠️ Please select at least one category above.")
        else:
            # 日期和结果数量选择
            col1, col2, col3 = st.columns([2, 2, 2])
            
            with col1:
                selected_date = st.date_input(
                    "📅 Select Date",
                    value=datetime.now(),
                    max_value=datetime.now(),
                    key="browse_date"
                )
            
            with col2:
                max_results = st.number_input(
                    "📊 Max Results",
                    min_value=10,
                    max_value=500,
                    value=100,
                    step=10,
                    key="browse_max_results"
                )
            
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                view_papers_btn = st.button("📖 View Papers", type="primary", use_container_width=True, key="view_papers_btn")
            
            # 获取并显示论文
            if view_papers_btn:
                with st.spinner("Loading papers..."):
                    data = api_get(
                        "/papers/arxiv/combined",
                        params={
                            "include": ",".join(st.session_state.selected_categories),
                            "date": selected_date.strftime("%Y-%m-%d"),
                            "limit": max_results
                        }
                    )
                
                if not data:
                    st.error("❌ Failed to load papers. Please check if the backend is running.")
                else:
                    papers = data.get("papers", [])
                    
                    if papers:
                        st.success(f"✅ Found {len(papers)} papers")
                        
                        # 论文筛选
                        with st.expander("🔍 Filter Papers", expanded=False):
                            filter_query = st.text_input("Filter by keywords (in title/abstract)", key="filter_query")
                            
                            if filter_query:
                                papers = [
                                    p for p in papers
                                    if filter_query.lower() in p.get("title", "").lower()
                                    or filter_query.lower() in p.get("abstract", "").lower()
                                ]
                                st.info(f"Filtered to {len(papers)} papers")
                        
                        st.markdown("---")
                        
                        # 显示论文列表
                        for paper in papers:
                            render_paper_card(paper)
                    else:
                        st.info("📭 No papers found for the selected date and categories.")
    
    # 标签页 2: 搜索论文
    with tab2:
        st.subheader("Search Papers by Keywords")
        
        # 搜索框
        col1, col2 = st.columns([5, 1])
        
        with col1:
            query = st.text_input(
                "🔍 Search Query",
                placeholder="e.g., transformer attention mechanism",
                key="search_input"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            search_btn = st.button("Go", type="primary", use_container_width=True, key="search_btn")
        
        # 搜索选项
        col1, col2 = st.columns(2)
        
        with col1:
            search_max_results = st.number_input(
                "📊 Max Results",
                min_value=10,
                max_value=1000,
                value=100,
                step=10,
                key="search_max_results"
            )
        
        with col2:
            # 使用上面选择的分类作为过滤器（可选）
            use_category_filter = st.checkbox(
                "Use selected categories as filter",
                value=False,
                key="use_cat_filter"
            )
        
        # 执行搜索
        if search_btn:
            if not query:
                st.warning("⚠️ Please enter a search query.")
            else:
                with st.spinner("Searching..."):
                    params = {
                        "query": query,
                        "max_results": search_max_results
                    }
                    
                    if use_category_filter and st.session_state.selected_categories:
                        params["categories"] = ",".join(st.session_state.selected_categories)
                    
                    data = api_get("/search/", params=params)
                
                if not data:
                    st.error("❌ Search failed. Please check if the backend is running.")
                else:
                    results = data.get("results", [])
                    
                    if results:
                        st.success(f"✅ Found {len(results)} papers")
                        st.markdown("---")
                        
                        # 显示搜索结果
                        for paper in results:
                            render_paper_card(paper)
                    else:
                        st.info("📭 No papers found for your query.")
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p><strong>Cool Papers</strong> - Made with ❤️ using Streamlit</p>
        <p>
            <a href="https://github.com/bojone/papers.cool" target="_blank">GitHub</a> | 
            <a href="https://kexue.fm/archives/9920" target="_blank">Blog</a> | 
            <a href="http://localhost:8000/docs" target="_blank">API Docs</a>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
