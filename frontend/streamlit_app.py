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

# 页面配置
st.set_page_config(
    page_title="Cool Papers",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
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
if "selected_venues" not in st.session_state:
    st.session_state.selected_venues = []


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

# 会议列表
VENUES = [
    "AAAI", "ACL", "COLM", "COLT", "CoRL", "CVPR", "ECCV", "EMNLP",
    "ICCV", "ICLR", "ICML", "IJCAI", "INTERSPEECH", "IWSLT", "MLSYS",
    "NAACL", "NDSS", "NeurIPS", "OSDI", "UAI", "USENIX-Fast", "USENIX-Sec"
]


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


def page_home():
    """首页 - 分类选择"""
    st.title("📚 Cool Papers")
    st.subheader("Immersive Paper Discovery（沉浸式刷论文！）")
    
    st.markdown("---")
    
    # ArXiv 分类
    st.header("🔬 arXiv Categories")
    st.caption("Select your interested categories")
    
    cols = st.columns(3)
    selected_cats = []
    
    for idx, (cat_name, cat_info) in enumerate(ARXIV_CATEGORIES.items()):
        with cols[idx % 3]:
            cat_id = cat_info[0]
            is_selected = cat_id in st.session_state.selected_categories
            
            if st.checkbox(cat_name, value=is_selected, key=f"cat_{cat_id}"):
                selected_cats.append(cat_id)
    
    st.session_state.selected_categories = selected_cats
    
    # 查看选中分类的论文
    if st.session_state.selected_categories:
        if st.button("📖 View Selected Categories", type="primary", use_container_width=True):
            st.session_state.page = "arxiv"
            st.rerun()
        
        # Feed 订阅链接
        feed_url = f"{API_BASE_URL}/feeds/arxiv/{','.join(st.session_state.selected_categories)}"
        st.caption(f"📡 RSS Feed: [{feed_url}]({feed_url})")
    
    st.markdown("---")
    
    # 会议论文
    st.header("🎓 Conference Papers (Venue)")
    st.caption("Browse papers from top conferences")
    
    cols = st.columns(6)
    for idx, venue in enumerate(VENUES):
        with cols[idx % 6]:
            if st.button(venue, key=f"venue_{venue}", use_container_width=True):
                st.session_state.selected_venue = venue
                st.session_state.page = "venue"
                st.rerun()
    
    st.markdown("---")
    
    # 搜索入口
    st.header("🔍 Search Papers")
    col1, col2 = st.columns([5, 1])
    
    with col1:
        query = st.text_input("Search by keywords", placeholder="transformer attention mechanism", label_visibility="collapsed")
    
    with col2:
        if st.button("Go", type="primary", use_container_width=True):
            if query:
                st.session_state.search_query = query
                st.session_state.page = "search"
                st.rerun()
    
    st.markdown("---")
    
    # 统计信息
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("⭐ Starred Papers", len(st.session_state.starred_papers))
    
    with col2:
        st.metric("👀 Viewed Papers", len(st.session_state.viewed_papers))
    
    with col3:
        st.metric("📂 Selected Categories", len(st.session_state.selected_categories))


def page_arxiv():
    """ArXiv 论文列表页面"""
    st.title("📚 arXiv Papers")
    
    # 返回首页按钮
    if st.button("🏠 Home", key="home_btn"):
        st.session_state.page = "home"
        st.rerun()
    
    # 显示选中的分类
    if not st.session_state.selected_categories:
        st.warning("Please select at least one category from the home page.")
        return
    
    st.subheader(f"Categories: {', '.join(st.session_state.selected_categories)}")
    
    # 日期选择
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        selected_date = st.date_input(
            "Select date",
            value=datetime.now(),
            max_value=datetime.now(),
            key="arxiv_date"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Latest", "Most Viewed", "Most Starred"],
            key="sort_by"
        )
    
    with col3:
        max_results = st.number_input(
            "Max results",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            key="max_results"
        )
    
    # 获取论文列表
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
        st.error("Failed to load papers. Please check if the backend is running.")
        return
    
    papers = data.get("papers", [])
    
    st.success(f"Found {len(papers)} papers")
    
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
    
    # 显示论文列表
    if papers:
        for paper in papers:
            render_paper_card(paper)
    else:
        st.info("No papers found.")
    
    # 底部导航栏
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 Home", key="bottom_home"):
            st.session_state.page = "home"
            st.rerun()
    
    with col2:
        if st.button("⭐ Starred Papers", key="view_starred"):
            st.session_state.page = "starred"
            st.rerun()
    
    with col3:
        # Feed 订阅
        feed_url = f"{API_BASE_URL}/feeds/arxiv/{','.join(st.session_state.selected_categories)}"
        st.link_button("📡 RSS Feed", feed_url)


def page_search():
    """搜索页面"""
    st.title("🔍 Search Papers")
    
    # 返回首页按钮
    if st.button("🏠 Home", key="home_btn"):
        st.session_state.page = "home"
        st.rerun()
    
    # 搜索框
    col1, col2 = st.columns([5, 1])
    
    with col1:
        query = st.text_input(
            "Search query",
            value=st.session_state.get("search_query", ""),
            placeholder="Enter keywords...",
            key="search_input"
        )
    
    with col2:
        search_btn = st.button("Go", type="primary", use_container_width=True)
    
    if not query:
        st.info("Enter a search query to find papers.")
        return
    
    # 搜索选项
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_results = st.number_input("Max results", min_value=10, max_value=1000, value=100, step=10)
    
    with col2:
        venue_filter = st.selectbox("Venue", ["All"] + VENUES)
    
    with col3:
        cat_filter = st.multiselect("Categories", [cat[0] for cat in ARXIV_CATEGORIES.values()])
    
    # 执行搜索
    if query:
        with st.spinner("Searching..."):
            params = {
                "query": query,
                "max_results": max_results
            }
            
            if venue_filter != "All":
                params["venue"] = venue_filter
            
            if cat_filter:
                params["categories"] = ",".join(cat_filter)
            
            data = api_get("/search/", params=params)
        
        if not data:
            st.error("Search failed. Please check if the backend is running.")
            return
        
        results = data.get("results", [])
        
        st.success(f"Found {len(results)} papers")
        
        # 显示搜索结果
        if results:
            for paper in results:
                render_paper_card(paper)
        else:
            st.info("No papers found for your query.")


def page_venue():
    """会议论文页面"""
    venue = st.session_state.get("selected_venue", "")
    
    if not venue:
        st.warning("No venue selected.")
        return
    
    st.title(f"🎓 {venue} Papers")
    
    # 返回首页按钮
    if st.button("🏠 Home", key="home_btn"):
        st.session_state.page = "home"
        st.rerun()
    
    # 获取会议论文
    with st.spinner(f"Loading {venue} papers..."):
        data = api_get(f"/papers/venue/{venue}")
    
    if not data:
        st.error("Failed to load papers. Please check if the backend is running.")
        return
    
    papers = data.get("papers", [])
    
    st.success(f"Found {len(papers)} papers from {venue}")
    
    # Feed 订阅
    feed_url = f"{API_BASE_URL}/feeds/venue/{venue}"
    st.caption(f"📡 RSS Feed: [{feed_url}]({feed_url})")
    
    st.markdown("---")
    
    # 显示论文列表
    if papers:
        for paper in papers:
            render_paper_card(paper)
    else:
        st.info(f"No papers found for {venue}.")


def page_starred():
    """星标论文页面"""
    st.title("⭐ Starred Papers")
    
    # 返回按钮
    if st.button("🏠 Home", key="home_btn"):
        st.session_state.page = "home"
        st.rerun()
    
    if not st.session_state.starred_papers:
        st.info("You haven't starred any papers yet.")
        return
    
    st.success(f"You have {len(st.session_state.starred_papers)} starred papers")
    
    # 导出按钮
    if st.button("📤 Export Starred Papers", type="primary"):
        export_data = {
            "starred_papers": list(st.session_state.starred_papers),
            "export_date": datetime.now().isoformat()
        }
        st.download_button(
            "💾 Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"starred_papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    st.markdown("---")
    
    # 显示星标论文
    # 注意：这里需要从后端获取完整的论文信息
    for paper_id in st.session_state.starred_papers:
        # 尝试从 arXiv 获取
        with st.spinner(f"Loading {paper_id}..."):
            if "@" in paper_id:
                source, pid = paper_id.split("@")
                data = api_get(f"/papers/{source.lower()}/{pid}")
            else:
                data = api_get(f"/papers/arxiv/{paper_id}")
        
        if data:
            render_paper_card(data)


def main():
    """主应用"""
    
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
    </style>
    """, unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=📚", width=150)
        st.title("Cool Papers")
        
        st.markdown("---")
        
        # 页面导航
        page = st.radio(
            "Navigation",
            ["🏠 Home", "📚 arXiv", "🔍 Search", "🎓 Venue", "⭐ Starred"],
            key="nav_radio"
        )
        
        # 更新页面状态
        page_map = {
            "🏠 Home": "home",
            "📚 arXiv": "arxiv",
            "🔍 Search": "search",
            "🎓 Venue": "venue",
            "⭐ Starred": "starred"
        }
        st.session_state.page = page_map[page]
        
        st.markdown("---")
        
        # 统计
        st.metric("⭐ Starred", len(st.session_state.starred_papers))
        st.metric("👀 Viewed", len(st.session_state.viewed_papers))
        
        st.markdown("---")
        
        # 关于
        st.caption("**About**")
        st.caption("Cool Papers - Immersive Paper Discovery")
        st.caption("[GitHub](https://github.com/bojone/papers.cool)")
        st.caption("[Blog](https://kexue.fm/archives/9920)")
    
    # 路由到不同页面
    current_page = st.session_state.get("page", "home")
    
    if current_page == "home":
        page_home()
    elif current_page == "arxiv":
        page_arxiv()
    elif current_page == "search":
        page_search()
    elif current_page == "venue":
        page_venue()
    elif current_page == "starred":
        page_starred()
    else:
        page_home()


if __name__ == "__main__":
    main()
