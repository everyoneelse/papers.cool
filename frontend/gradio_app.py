"""
Cool Papers - Simplified Gradio Frontend
简化的Gradio前端 - 单页面论文浏览和搜索
"""

import gradio as gr
from datetime import datetime
import pandas as pd
from typing import List, Dict, Optional, Tuple
import json
import os
from pathlib import Path

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

# Tantivy搜索索引路径
SEARCH_INDEX_PATH = os.getenv("SEARCH_INDEX_PATH", "./search_index")


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
        print(f"Error loading papers from {json_file}: {e}")
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


def format_papers_dataframe(papers: List[Dict]) -> pd.DataFrame:
    """
    将论文列表格式化为pandas DataFrame
    包含：标题、作者、摘要、分类
    """
    if not papers:
        return pd.DataFrame(columns=["Title", "Authors", "Abstract", "Categories", "URL"])
    
    data = []
    for paper in papers:
        title = paper.get("title", "Untitled")
        url = paper.get("url", "") or paper.get("pdf_url", "")
        
        # 创建带链接的标题（使用HTML）
        if url:
            title_with_link = f'<a href="{url}" target="_blank">{title}</a>'
        else:
            title_with_link = title
        
        # 作者列表
        authors = paper.get("authors", [])
        if isinstance(authors, list):
            if len(authors) > 5:
                authors_str = ", ".join(authors[:5]) + " et al."
            else:
                authors_str = ", ".join(authors)
        else:
            authors_str = str(authors)
        
        # 摘要
        abstract = paper.get("abstract", "No abstract available.")
        if len(abstract) > 200:
            abstract = abstract[:200] + "..."
        
        # 分类
        categories = paper.get("categories", [])
        if isinstance(categories, list):
            categories_str = ", ".join(categories)
        else:
            categories_str = str(categories)
        
        data.append({
            "Title": title_with_link,
            "Authors": authors_str,
            "Abstract": abstract,
            "Categories": categories_str,
            "URL": url
        })
    
    df = pd.DataFrame(data)
    return df[["Title", "Authors", "Abstract", "Categories"]]  # 不显示URL列，已经在标题中


def search_papers_with_tantivy(query: str, papers: List[Dict]) -> List[Dict]:
    """
    使用Tantivy搜索论文（搜索标题和摘要）
    注：这里是简化实现，实际需要安装tantivy-py并构建索引
    
    如果没有安装tantivy，这里使用简单的字符串匹配作为fallback
    """
    if not query:
        return papers
    
    query_lower = query.lower()
    results = []
    
    for paper in papers:
        title = paper.get("title", "").lower()
        abstract = paper.get("abstract", "").lower()
        
        # 简单的字符串匹配（作为tantivy的替代）
        if query_lower in title or query_lower in abstract:
            results.append(paper)
    
    return results


def load_and_display_papers(
    selected_date: str,
    selected_categories: List[str]
) -> Tuple[pd.DataFrame, str]:
    """
    加载并显示指定日期和分类的论文
    """
    if not selected_date:
        return pd.DataFrame(), "❌ Please select a date"
    
    # 加载论文
    papers = load_papers_from_json(selected_date)
    
    if not papers:
        return pd.DataFrame(), f"📭 No papers found for date {selected_date}"
    
    # 根据分类过滤
    filtered_papers = filter_papers_by_categories(papers, selected_categories)
    
    if not filtered_papers:
        return pd.DataFrame(), f"📭 No papers found in selected categories for {selected_date}"
    
    # 格式化为DataFrame
    df = format_papers_dataframe(filtered_papers)
    
    status_msg = f"✅ Found {len(filtered_papers)} papers for {selected_date}"
    return df, status_msg


def search_and_display(
    query: str,
    selected_date: str,
    selected_categories: List[str]
) -> Tuple[pd.DataFrame, str]:
    """
    在当前日期的论文中搜索
    """
    if not query:
        return pd.DataFrame(), "⚠️ Please enter a search query"
    
    if not selected_date:
        return pd.DataFrame(), "❌ Please select a date first"
    
    # 加载当前日期的论文
    papers = load_papers_from_json(selected_date)
    
    if not papers:
        return pd.DataFrame(), f"📭 No papers found for date {selected_date}"
    
    # 根据分类过滤
    filtered_papers = filter_papers_by_categories(papers, selected_categories)
    
    # 使用tantivy搜索
    search_results = search_papers_with_tantivy(query, filtered_papers)
    
    if not search_results:
        return pd.DataFrame(), f"📭 No results found for query: '{query}'"
    
    # 格式化为DataFrame
    df = format_papers_dataframe(search_results)
    
    status_msg = f"🔍 Found {len(search_results)} results for '{query}' in {selected_date}"
    return df, status_msg


def create_app():
    """创建简化的Gradio应用"""
    
    with gr.Blocks(
        title="Cool Papers - Simple Interface",
        theme=gr.themes.Soft(primary_hue="green")
    ) as app:
        
        # 标题
        gr.Markdown("""
        # 📚 Cool Papers - Paper Browser & Search
        ### Browse arXiv papers by category and date, or search within a specific date
        """)
        
        # 日期选择
        with gr.Row():
            date_selector = gr.Textbox(
                label="📅 Date (YYYY-MM-DD)",
                value=datetime.now().strftime("%Y-%m-%d"),
                placeholder="2025-11-13"
            )
        
        # 分类选择 - 使用Dropdown支持多选
        with gr.Row():
            category_selector = gr.Dropdown(
                choices=list(ARXIV_CATEGORIES.keys()),
                value=["Artificial Intelligence (cs.AI)", "Machine Learning (cs.LG)"],
                label="🔬 Select Categories (Multi-select)",
                multiselect=True,
                interactive=True
            )
        
        # 状态信息
        status_text = gr.Textbox(
            label="Status",
            value="Select a date and categories to view papers",
            interactive=False
        )
        
        # 论文显示区域 - 使用DataFrame
        papers_table = gr.DataFrame(
            label="📄 Papers",
            headers=["Title", "Authors", "Abstract", "Categories"],
            datatype=["html", "str", "str", "str"],
            wrap=True,
            height=400
        )
        
        # 分隔线
        gr.Markdown("---")
        gr.Markdown("### 🔍 Search Papers")
        
        # 搜索区域
        with gr.Row():
            search_box = gr.Textbox(
                label="Search Query",
                placeholder="Enter keywords to search in titles and abstracts...",
                scale=4
            )
            search_button = gr.Button("🔍 Search", variant="primary", scale=1)
        
        # 搜索结果
        search_status = gr.Textbox(
            label="Search Status",
            value="Enter a query and click Search",
            interactive=False
        )
        
        search_results_table = gr.DataFrame(
            label="🔍 Search Results",
            headers=["Title", "Authors", "Abstract", "Categories"],
            datatype=["html", "str", "str", "str"],
            wrap=True,
            height=400
        )
        
        # 事件绑定 - 当日期或分类变化时自动加载论文
        date_selector.change(
            fn=load_and_display_papers,
            inputs=[date_selector, category_selector],
            outputs=[papers_table, status_text]
        )
        
        category_selector.change(
            fn=load_and_display_papers,
            inputs=[date_selector, category_selector],
            outputs=[papers_table, status_text]
        )
        
        # 搜索按钮点击事件
        search_button.click(
            fn=search_and_display,
            inputs=[search_box, date_selector, category_selector],
            outputs=[search_results_table, search_status]
        )
        
        # 页脚
        gr.Markdown("""
        ---
        <div style="text-align: center; color: #666;">
            <p><strong>Cool Papers</strong> - Simplified Interface</p>
            <p>Data loaded from local JSON files</p>
        </div>
        """)
    
    return app


def main():
    """主函数"""
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    
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
