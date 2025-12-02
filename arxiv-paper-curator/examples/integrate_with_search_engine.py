"""
集成示例：将 arXiv Advanced Search 集成到你的搜索引擎中

展示如何在现有的 search_engine.py 基础上添加官方搜索验证功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "frontend"))

from src.scripts.arxiv_advanced_search import ArxivAdvancedSearch
from datetime import datetime
import json


class EnhancedPaperSearch:
    """
    增强的论文搜索引擎
    
    结合本地搜索和 arXiv 官方搜索，提供数据验证功能
    """
    
    def __init__(self, local_data_dir: str = "./papers_data"):
        self.local_data_dir = Path(local_data_dir)
        self.arxiv_searcher = ArxivAdvancedSearch()
    
    def load_local_papers(self, date: datetime, categories: list) -> dict:
        """加载本地论文数据"""
        papers_by_category = {}
        date_str = date.strftime('%Y-%m-%d')
        
        for category in categories:
            category_file = self.local_data_dir / category / f"papers_{date_str}_100percent.json"
            
            if category_file.exists():
                with open(category_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    papers_by_category[category] = data.get('papers', [])
            else:
                papers_by_category[category] = []
        
        return papers_by_category
    
    def search_with_validation(
        self,
        keywords: str,
        date: datetime,
        categories: list,
        validate: bool = True
    ):
        """
        搜索论文并可选地验证数据完整性
        
        Args:
            keywords: 搜索关键词
            date: 目标日期
            categories: 分类列表
            validate: 是否与 arXiv 官方验证
            
        Returns:
            搜索结果和验证报告（如果启用）
        """
        # 1. 从本地数据搜索
        print(f"🔍 Searching local data for '{keywords}' on {date.strftime('%Y-%m-%d')}...")
        local_papers = self.load_local_papers(date, categories)
        
        # 简单的关键词匹配（你可以替换为 BM25 搜索）
        local_results = []
        for category, papers in local_papers.items():
            for paper in papers:
                if self._keyword_match(keywords, paper):
                    local_results.append({
                        **paper,
                        'source': 'local',
                        'category': category
                    })
        
        print(f"✓ Found {len(local_results)} papers in local data")
        
        # 2. 可选：从 arXiv 官方搜索验证
        validation_report = None
        if validate:
            print(f"\n🌐 Validating with arXiv official search...")
            
            arxiv_results = self.arxiv_searcher.search(
                keywords=keywords,
                categories=categories,
                date_from=date,
                date_to=date,
                max_results=1000
            )
            
            print(f"✓ Found {len(arxiv_results)} papers on arXiv")
            
            # 比较结果
            local_ids = set(p.get('arxiv_id', '').split('v')[0] for p in local_results)
            arxiv_ids = set(p['arxiv_id'].split('v')[0] for p in arxiv_results)
            
            matched = local_ids & arxiv_ids
            missing_in_local = arxiv_ids - local_ids
            extra_in_local = local_ids - arxiv_ids
            
            match_rate = len(matched) / len(arxiv_ids) * 100 if arxiv_ids else 100
            
            validation_report = {
                'local_count': len(local_results),
                'arxiv_count': len(arxiv_results),
                'matched': len(matched),
                'match_rate': match_rate,
                'missing_in_local': list(missing_in_local),
                'extra_in_local': list(extra_in_local),
            }
            
            print(f"\n📊 Validation Results:")
            print(f"  Match rate: {match_rate:.1f}%")
            print(f"  Local: {len(local_results)}, arXiv: {len(arxiv_results)}, Matched: {len(matched)}")
            
            if missing_in_local:
                print(f"  ⚠️  Missing in local: {len(missing_in_local)} papers")
                for arxiv_id in list(missing_in_local)[:3]:
                    print(f"     - {arxiv_id}")
        
        return {
            'results': local_results,
            'validation': validation_report
        }
    
    def _keyword_match(self, keywords: str, paper: dict) -> bool:
        """简单的关键词匹配"""
        keywords_lower = keywords.lower()
        
        # 在标题和摘要中搜索
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        
        return keywords_lower in title or keywords_lower in abstract
    
    def verify_date_completeness(
        self,
        date: datetime,
        categories: list = None
    ) -> dict:
        """
        验证指定日期的数据完整性
        
        Args:
            date: 目标日期
            categories: 分类列表（默认：所有 AI 分类）
            
        Returns:
            完整性报告
        """
        if categories is None:
            categories = ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "cs.NE", "cs.CC", "stat.ML"]
        
        print(f"\n{'='*80}")
        print(f"📋 Data Completeness Verification for {date.strftime('%Y-%m-%d')}")
        print(f"{'='*80}")
        
        # 加载本地数据
        local_papers = self.load_local_papers(date, categories)
        
        # 从 arXiv 获取官方数据
        print(f"\n🌐 Fetching from arXiv API...")
        arxiv_results = self.arxiv_searcher.search_by_date_and_category(
            date=date,
            categories=categories
        )
        
        # 按分类对比
        report = {
            'date': date.strftime('%Y-%m-%d'),
            'categories': {},
            'summary': {
                'total_local': 0,
                'total_arxiv': 0,
                'total_matched': 0,
                'overall_match_rate': 0,
            }
        }
        
        for category in categories:
            local = local_papers.get(category, [])
            arxiv = arxiv_results.get(category, [])
            
            local_ids = set(p.get('arxiv_id', '').split('v')[0] for p in local if p.get('arxiv_id'))
            arxiv_ids = set(p['arxiv_id'].split('v')[0] for p in arxiv)
            
            matched = local_ids & arxiv_ids
            missing = arxiv_ids - local_ids
            extra = local_ids - arxiv_ids
            
            match_rate = len(matched) / len(arxiv_ids) * 100 if arxiv_ids else 100
            
            report['categories'][category] = {
                'local_count': len(local),
                'arxiv_count': len(arxiv),
                'matched': len(matched),
                'match_rate': match_rate,
                'missing_count': len(missing),
                'extra_count': len(extra),
                'status': '✅' if match_rate == 100 else ('✓' if match_rate >= 95 else '⚠️')
            }
            
            report['summary']['total_local'] += len(local)
            report['summary']['total_arxiv'] += len(arxiv)
            report['summary']['total_matched'] += len(matched)
        
        # 计算总体匹配率
        if report['summary']['total_arxiv'] > 0:
            report['summary']['overall_match_rate'] = (
                report['summary']['total_matched'] / report['summary']['total_arxiv'] * 100
            )
        
        # 打印报告
        print(f"\n{'='*80}")
        print(f"📊 Summary:")
        print(f"  Total Local:  {report['summary']['total_local']}")
        print(f"  Total arXiv:  {report['summary']['total_arxiv']}")
        print(f"  Match Rate:   {report['summary']['overall_match_rate']:.2f}%")
        print(f"\n📋 By Category:")
        
        for cat, cat_report in report['categories'].items():
            print(f"  {cat_report['status']} {cat}: "
                  f"{cat_report['local_count']} local, {cat_report['arxiv_count']} arXiv, "
                  f"{cat_report['match_rate']:.1f}% match")
        
        print(f"{'='*80}\n")
        
        return report


def demo_basic_search():
    """演示基本搜索功能"""
    print("\n" + "="*80)
    print("📝 Demo 1: Basic Search with Validation")
    print("="*80)
    
    engine = EnhancedPaperSearch()
    
    # 搜索示例（使用一个你有数据的日期）
    # 注意：请替换为你实际有数据的日期
    target_date = datetime(2024, 11, 25)
    
    result = engine.search_with_validation(
        keywords="large language model",
        date=target_date,
        categories=["cs.AI", "cs.CL"],
        validate=True  # 启用验证
    )
    
    print(f"\n✅ Search completed")
    print(f"   Found {len(result['results'])} papers")
    
    if result['validation']:
        print(f"   Validation: {result['validation']['match_rate']:.1f}% match rate")


def demo_completeness_check():
    """演示完整性检查"""
    print("\n" + "="*80)
    print("📝 Demo 2: Data Completeness Check")
    print("="*80)
    
    engine = EnhancedPaperSearch()
    
    # 检查指定日期的数据完整性
    target_date = datetime(2024, 11, 25)
    
    report = engine.verify_date_completeness(
        date=target_date,
        categories=["cs.AI", "cs.CV"]  # 只检查部分分类以节省时间
    )
    
    # 保存报告
    output_dir = Path(__file__).parent / "validation_output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"completeness_{target_date.strftime('%Y-%m-%d')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Report saved to: {output_file}")


def demo_custom_integration():
    """演示如何集成到你的现有代码"""
    print("\n" + "="*80)
    print("📝 Demo 3: Integration with Existing Search Engine")
    print("="*80)
    
    # 假设你已经有 search_engine.py 的 PaperSearchEngine
    # 这里展示如何添加验证功能
    
    print("""
你可以这样集成到现有的 search_engine.py：

```python
from search_engine import PaperSearchEngine
from src.scripts.arxiv_advanced_search import ArxivAdvancedSearch

class ValidatedSearchEngine(PaperSearchEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arxiv_searcher = ArxivAdvancedSearch()
    
    def search_with_validation(self, query, date, categories):
        # 1. 使用本地 BM25 搜索
        local_results = self.search(query, max_results=100)
        
        # 2. 从 arXiv 验证
        arxiv_results = self.arxiv_searcher.search(
            keywords=query,
            categories=categories,
            date_from=date,
            date_to=date
        )
        
        # 3. 对比结果
        # ... (参考 EnhancedPaperSearch 的实现)
        
        return local_results, arxiv_results
```

然后在你的 Streamlit 应用中：

```python
# 在 frontend 代码中
engine = ValidatedSearchEngine()

if st.button("Validate Data Completeness"):
    report = engine.verify_completeness(selected_date, selected_categories)
    st.json(report)
```
    """)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 Enhanced Paper Search - Integration Examples")
    print("="*80)
    print("\n这个脚本展示如何将 arXiv Advanced Search 集成到你的搜索引擎中")
    print("\n⚠️  注意：以下示例需要你有对应日期的本地数据")
    print("   如果没有，请先运行: python src/scripts/fetch_daily_papers_100percent.py --date YYYY-MM-DD")
    print("="*80)
    
    # 运行演示
    # 注意：这些演示需要实际的数据，你可以根据需要注释/取消注释
    
    # demo_basic_search()  # 需要本地数据
    # demo_completeness_check()  # 需要本地数据和网络连接
    demo_custom_integration()  # 只展示代码，不需要数据
    
    print("\n" + "="*80)
    print("✅ Integration examples completed!")
    print("\n💡 Next steps:")
    print("  1. 在你的 search_engine.py 中添加 ArxivAdvancedSearch")
    print("  2. 在 Streamlit UI 中添加 '验证数据完整性' 按钮")
    print("  3. 定期运行完整性检查以确保数据质量")
    print("="*80 + "\n")

