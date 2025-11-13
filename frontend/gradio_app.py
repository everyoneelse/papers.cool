"""
Cool Papers - Gradio Frontend
沉浸式刷论文！Immersive Paper Discovery
"""

import gradio as gr
from datetime import datetime, timedelta
import httpx
from typing import List, Dict, Optional, Tuple
import json
import os

# 后端 API 地址
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

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

# 全局状态（使用 gradio.State）
starred_papers_global = set()
viewed_papers_global = set()


def api_get(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """调用后端 API"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_BASE_URL}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}


def format_paper_card(paper: Dict, starred_papers: set) -> str:
    """格式化单个论文卡片为 HTML"""
    paper_id = paper.get("id", "")
    is_starred = paper_id in starred_papers
    star_icon = "⭐" if is_starred else "☆"
    
    # 论文标题
    title = paper.get("title", "Untitled")
    title_prefix = f"**#{paper_id.split('@')[0] if '@' in paper_id else paper_id}**" if paper_id else ""
    
    # 作者
    authors = paper.get("authors", [])
    if authors:
        if len(authors) > 5:
            author_str = ", ".join(authors[:5]) + " et al."
        else:
            author_str = ", ".join(authors)
    else:
        author_str = "Unknown"
    
    # 分类和发布日期
    categories = paper.get("categories", [])
    category_str = ", ".join(categories[:3]) if categories else "N/A"
    pub_date = paper.get("published_date", "N/A")
    
    # 摘要
    abstract = paper.get("abstract", "No abstract available.")
    if len(abstract) > 300:
        abstract = abstract[:300] + "..."
    
    # 链接
    pdf_url = paper.get("pdf_url", "")
    paper_url = paper.get("url", "")
    
    # 构建 HTML 卡片
    html = f"""
    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 20px; margin: 10px 0; background-color: #f9f9f9;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; color: #32a852;">{star_icon} {title_prefix} {title}</h3>
        </div>
        <p style="color: #666; margin: 10px 0;"><strong>👥 Authors:</strong> {author_str}</p>
        <div style="display: flex; gap: 20px; margin: 10px 0;">
            <p style="color: #666; margin: 0;"><strong>🏷️ Categories:</strong> {category_str}</p>
            <p style="color: #666; margin: 0;"><strong>📅 Published:</strong> {pub_date}</p>
        </div>
        <details style="margin: 15px 0;">
            <summary style="cursor: pointer; color: #32a852; font-weight: bold;">📄 Abstract</summary>
            <p style="margin-top: 10px; line-height: 1.6;">{abstract}</p>
        </details>
        <div style="display: flex; gap: 10px; margin-top: 15px;">
            {f'<a href="{pdf_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #32a852; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">📄 PDF</button></a>' if pdf_url else ''}
            {f'<a href="{paper_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">🔗 Link</button></a>' if paper_url else ''}
            <button onclick="alert('Kimi summary coming soon!')" style="background-color: #2196F3; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">🤖 Kimi</button>
        </div>
    </div>
    """
    return html


def format_papers_list(papers: List[Dict], starred_papers: set) -> str:
    """格式化论文列表"""
    if not papers:
        return "<p style='text-align: center; color: #666;'>📭 No papers found.</p>"
    
    html = f"<div style='margin: 20px 0;'><h3 style='color: #32a852;'>Found {len(papers)} papers</h3></div>"
    for paper in papers:
        html += format_paper_card(paper, starred_papers)
    
    return html


def fetch_arxiv_papers(
    selected_categories: List[str],
    selected_date: float,
    max_results: int,
    starred_papers: set
) -> Tuple[str, set]:
    """获取 arXiv 论文"""
    if not selected_categories:
        return "<p style='color: orange;'>⚠️ Please select at least one category.</p>", starred_papers
    
    # 转换分类名称为代码
    category_codes = [ARXIV_CATEGORIES.get(cat, cat) for cat in selected_categories]
    
    # 格式化日期 - gr.DateTime 返回的是 float 时间戳
    if selected_date:
        date_obj = datetime.fromtimestamp(selected_date)
        date_str = date_obj.strftime("%Y-%m-%d")
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 调用 API
    data = api_get(
        "/papers/arxiv/combined",
        params={
            "include": ",".join(category_codes),
            "date": date_str,
            "limit": max_results
        }
    )
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unknown error") if data else "API connection failed"
        return f"<p style='color: red;'>❌ Error: {error_msg}</p>", starred_papers
    
    papers = data.get("papers", [])
    return format_papers_list(papers, starred_papers), starred_papers


def search_papers(
    query: str,
    max_results: int,
    category_filter: List[str],
    starred_papers: set
) -> Tuple[str, set]:
    """搜索论文"""
    if not query:
        return "<p style='color: orange;'>⚠️ Please enter a search query.</p>", starred_papers
    
    params = {
        "query": query,
        "max_results": max_results
    }
    
    if category_filter:
        category_codes = [ARXIV_CATEGORIES.get(cat, cat) for cat in category_filter]
        params["categories"] = ",".join(category_codes)
    
    data = api_get("/search/", params=params)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unknown error") if data else "API connection failed"
        return f"<p style='color: red;'>❌ Error: {error_msg}</p>", starred_papers
    
    results = data.get("results", [])
    return format_papers_list(results, starred_papers), starred_papers


def toggle_star_paper(paper_id: str, starred_papers: set) -> Tuple[str, set]:
    """切换论文星标状态"""
    if paper_id in starred_papers:
        starred_papers.discard(paper_id)
        return f"✅ Removed {paper_id} from starred papers", starred_papers
    else:
        starred_papers.add(paper_id)
        return f"⭐ Added {paper_id} to starred papers", starred_papers


def export_starred_papers(starred_papers: set) -> str:
    """导出星标论文"""
    if not starred_papers:
        return json.dumps({"message": "No starred papers to export"}, indent=2)
    
    export_data = {
        "starred_papers": list(starred_papers),
        "export_date": datetime.now().isoformat(),
        "count": len(starred_papers)
    }
    return json.dumps(export_data, indent=2)




def create_main_interface(starred_papers_state):
    """创建统一的主界面（无侧边栏，无标签页）"""
    
    # arXiv 分类选择 - 放在最上方
    gr.Markdown("## 🔬 arXiv Categories")
    selected_categories = gr.CheckboxGroup(
        choices=list(ARXIV_CATEGORIES.keys()),
        value=["Artificial Intelligence (cs.AI)", "Computation and Language (cs.CL)", "Machine Learning (cs.LG)"],
        label="Select Categories to Browse",
        interactive=True
    )
    
    # 浏览和搜索选项卡
    with gr.Tabs():
        # arXiv 浏览标签
        with gr.Tab("📅 Browse by Date"):
            gr.Markdown("### Browse arXiv Papers by Date and Categories")
            
            with gr.Row():
                with gr.Column(scale=1):
                    selected_date = gr.DateTime(
                        label="📅 Select Date",
                        value=datetime.now(),
                        include_time=False
                    )
                
                with gr.Column(scale=1):
                    max_results = gr.Slider(
                        minimum=10,
                        maximum=500,
                        value=100,
                        step=10,
                        label="📊 Max Results"
                    )
            
            browse_button = gr.Button("📚 View Papers", variant="primary", size="lg")
            papers_output = gr.HTML(label="Papers", value="<p style='text-align: center;'>Select categories above and click 'View Papers' to load.</p>")
            
            # 绑定浏览事件
            browse_button.click(
                fn=fetch_arxiv_papers,
                inputs=[selected_categories, selected_date, max_results, starred_papers_state],
                outputs=[papers_output, starred_papers_state]
            )
            
            # 也支持自动加载
            selected_categories.change(
                fn=fetch_arxiv_papers,
                inputs=[selected_categories, selected_date, max_results, starred_papers_state],
                outputs=[papers_output, starred_papers_state]
            )
            
            selected_date.change(
                fn=fetch_arxiv_papers,
                inputs=[selected_categories, selected_date, max_results, starred_papers_state],
                outputs=[papers_output, starred_papers_state]
            )
        
        # 搜索标签
        with gr.Tab("🔍 Search Papers"):
            gr.Markdown("### Search Papers by Keywords")
            
            with gr.Row():
                search_query = gr.Textbox(
                    label="Search Query",
                    placeholder="e.g., transformer attention mechanism",
                    scale=4
                )
                search_button = gr.Button("🔍 Search", variant="primary", scale=1)
            
            with gr.Row():
                search_max_results = gr.Slider(
                    minimum=10,
                    maximum=1000,
                    value=100,
                    step=10,
                    label="📊 Max Results"
                )
            
            gr.Markdown("**Tip:** Search will use the categories selected above. Deselect all to search across all categories.")
            
            search_results = gr.HTML(label="Search Results", value="<p style='text-align: center;'>Enter a query and click 'Search'.</p>")
            
            # 绑定搜索事件
            search_button.click(
                fn=search_papers,
                inputs=[search_query, search_max_results, selected_categories, starred_papers_state],
                outputs=[search_results, starred_papers_state]
            )






def create_app():
    """创建 Gradio 应用"""
    
    # 自定义 CSS
    custom_css = """
    .gradio-container {
        font-family: 'Arial', sans-serif;
    }
    
    h1, h2, h3 {
        color: #32a852;
    }
    
    .gr-button-primary {
        background-color: #32a852 !important;
        border-color: #32a852 !important;
    }
    
    .gr-button-primary:hover {
        background-color: #2d9647 !important;
    }
    
    details {
        cursor: pointer;
    }
    
    details summary {
        font-weight: bold;
        color: #32a852;
    }
    """
    
    with gr.Blocks(
        title="Cool Papers - Gradio Frontend",
        css=custom_css,
        theme=gr.themes.Soft(primary_hue="green")
    ) as app:
        
        # 应用标题
        gr.Markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(90deg, #32a852 0%, #2d9647 100%); border-radius: 10px; margin-bottom: 20px;">
            <h1 style="color: white; margin: 0;">📚 Cool Papers</h1>
            <p style="color: white; margin: 10px 0 0 0;">Immersive Paper Discovery | 沉浸式刷论文</p>
        </div>
        """)
        
        # 全局状态：星标论文集合
        starred_papers_state = gr.State(set())
        
        # 创建标签页
        create_papers_tab(starred_papers_state)
        
        # 页脚
        gr.Markdown("""
        ---
        <div style="text-align: center; color: #666; padding: 20px;">
            <p><strong>Cool Papers</strong> - Made with ❤️ using Gradio</p>
            <p>
                <a href="https://github.com/bojone/papers.cool" target="_blank">GitHub</a> | 
                <a href="https://kexue.fm/archives/9920" target="_blank">Blog</a> | 
                <a href="http://localhost:8000/docs" target="_blank">API Docs</a>
            </p>
        </div>
        """)
    
    return app


def main():
    """主函数"""
    app = create_app()
    
    # 启动应用
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
