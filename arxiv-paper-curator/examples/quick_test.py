"""
快速测试脚本 - 验证 arXiv Advanced Search 功能

这个脚本可以快速测试 arXiv API 搜索功能，无需完整的对比流程
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scripts.arxiv_advanced_search import ArxivAdvancedSearch
from datetime import datetime, timedelta
import json


def test_basic_search():
    """测试基本搜索功能"""
    print("\n" + "=" * 80)
    print("🧪 Test 1: Basic Search (yesterday's cs.AI papers)")
    print("=" * 80)
    
    searcher = ArxivAdvancedSearch(delay_seconds=3.0)
    yesterday = datetime.now() - timedelta(days=1)
    
    results = searcher.search(
        categories=["cs.AI"],
        date_from=yesterday,
        date_to=yesterday,
        max_results=20,
    )
    
    print(f"\n✅ Found {len(results)} papers")
    
    if results:
        print("\n📄 Sample papers:")
        for i, paper in enumerate(results[:3], 1):
            print(f"\n  {i}. {paper['arxiv_id']}")
            print(f"     Title: {paper['title'][:80]}...")
            print(f"     Authors: {', '.join(paper['authors'][:3])}")
            print(f"     Categories: {', '.join(paper['categories'][:3])}")
    
    return results


def test_keyword_search():
    """测试关键词搜索"""
    print("\n" + "=" * 80)
    print("🧪 Test 2: Keyword Search ('large language model' in yesterday's papers)")
    print("=" * 80)
    
    searcher = ArxivAdvancedSearch(delay_seconds=3.0)
    yesterday = datetime.now() - timedelta(days=1)
    
    results = searcher.search(
        keywords="large language model",
        categories=["cs.AI", "cs.CL", "cs.LG"],
        date_from=yesterday,
        date_to=yesterday,
        max_results=50,
    )
    
    print(f"\n✅ Found {len(results)} papers containing 'large language model'")
    
    if results:
        print("\n📄 Sample papers:")
        for i, paper in enumerate(results[:3], 1):
            print(f"\n  {i}. {paper['arxiv_id']}")
            print(f"     Title: {paper['title']}")
            print(f"     Abstract: {paper['abstract'][:150]}...")
    
    return results


def test_multi_category_search():
    """测试多分类搜索"""
    print("\n" + "=" * 80)
    print("🧪 Test 3: Multi-Category Search (cs.AI, cs.CV, cs.LG)")
    print("=" * 80)
    
    searcher = ArxivAdvancedSearch(delay_seconds=3.0)
    yesterday = datetime.now() - timedelta(days=1)
    
    results_by_category = searcher.search_by_date_and_category(
        date=yesterday,
        categories=["cs.AI", "cs.CV", "cs.LG"],
    )
    
    print(f"\n✅ Results by category:")
    total = 0
    for category, papers in results_by_category.items():
        print(f"  - {category}: {len(papers)} papers")
        total += len(papers)
    
    print(f"\n  Total: {total} papers")
    
    return results_by_category


def save_test_results(results, filename="test_results.json"):
    """保存测试结果"""
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / filename
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


def main():
    print("\n" + "=" * 80)
    print("🚀 arXiv Advanced Search - Quick Test")
    print("=" * 80)
    print("\nThis script will test the arXiv API search functionality")
    print("with yesterday's papers (to ensure data availability)")
    print("\n⏱️  Note: Tests will take ~10-15 seconds due to API rate limits")
    print("=" * 80)
    
    try:
        # Test 1: Basic search
        results1 = test_basic_search()
        
        # Test 2: Keyword search
        results2 = test_keyword_search()
        
        # Test 3: Multi-category search
        results3 = test_multi_category_search()
        
        # Save results
        print("\n" + "=" * 80)
        print("💾 Saving test results...")
        save_test_results(results1, "test1_basic_search.json")
        save_test_results(results2, "test2_keyword_search.json")
        save_test_results(results3, "test3_multi_category.json")
        
        print("\n" + "=" * 80)
        print("✅ All tests completed successfully!")
        print("=" * 80)
        
        print("\n💡 Next steps:")
        print("  1. Check the test_output directory for detailed results")
        print("  2. Try the full comparison tool:")
        print("     python examples/compare_local_with_arxiv.py --date YYYY-MM-DD")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ Error during testing: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

