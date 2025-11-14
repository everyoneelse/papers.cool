#!/usr/bin/env python3
"""
测试 BM25 搜索引擎
"""
import json
from pathlib import Path
from search_engine import PaperSearchEngine, search_papers_bm25

def test_search_engine():
    """测试搜索引擎基本功能"""
    
    print("=" * 60)
    print("测试 BM25 搜索引擎")
    print("=" * 60)
    
    # 1. 加载测试数据
    print("\n1. 加载论文数据...")
    data_dir = Path("papers_data")
    json_files = list(data_dir.glob("papers_*.json"))
    
    if not json_files:
        print("❌ 未找到论文数据文件！")
        print(f"   请确保 {data_dir} 目录下有 papers_*.json 文件")
        return False
    
    # 使用最新的文件
    json_file = sorted(json_files)[-1]
    print(f"   使用文件: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取论文列表
    if isinstance(data, list):
        papers = data
    elif isinstance(data, dict) and 'papers' in data:
        papers = data['papers']
    else:
        print("❌ 无法解析论文数据格式！")
        return False
    
    print(f"   加载了 {len(papers)} 篇论文")
    
    # 2. 创建搜索引擎
    print("\n2. 初始化搜索引擎...")
    engine = PaperSearchEngine(index_path="./test_search_index")
    
    # 3. 构建索引
    print("\n3. 构建搜索索引...")
    engine.build_index_from_papers(papers)
    
    # 4. 查看索引状态
    stats = engine.get_index_stats()
    print(f"   索引状态: {stats}")
    
    if stats['num_documents'] == 0:
        print("❌ 索引构建失败！")
        return False
    
    print(f"   ✅ 索引构建成功，共 {stats['num_documents']} 篇论文")
    
    # 5. 测试搜索
    print("\n4. 测试搜索功能...")
    
    test_queries = [
        "transformer",
        "attention mechanism",
        "large language model",
        "neural network"
    ]
    
    for query in test_queries:
        print(f"\n   查询: '{query}'")
        results = engine.search(query, max_results=5)
        
        if results:
            print(f"   ✅ 找到 {len(results)} 个结果")
            for i, result in enumerate(results[:3], 1):
                print(f"      {i}. {result['title'][:80]}...")
                print(f"         Score: {result['search_score']:.4f}")
        else:
            print(f"   ⚠️ 未找到结果")
    
    # 6. 测试便捷函数
    print("\n5. 测试便捷函数...")
    results = search_papers_bm25(
        query="transformer",
        papers=papers,
        search_engine=engine
    )
    print(f"   ✅ search_papers_bm25 返回 {len(results)} 个结果")
    
    # 7. 清理
    print("\n6. 清理测试索引...")
    engine.clear_index()
    print("   ✅ 测试索引已清理")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    
    return True


def test_simple_usage():
    """测试最简单的使用方式"""
    
    print("\n" + "=" * 60)
    print("测试简单使用方式")
    print("=" * 60)
    
    # 模拟论文数据
    papers = [
        {
            "id": "2301.00001",
            "arxiv_id": "2301.00001",
            "title": "Attention Is All You Need",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "categories": ["cs.AI", "cs.LG"],
            "published_date": "2023-01-01"
        },
        {
            "id": "2301.00002",
            "arxiv_id": "2301.00002",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "abstract": "We introduce a new language representation model called BERT.",
            "authors": ["Jacob Devlin", "Ming-Wei Chang"],
            "categories": ["cs.CL", "cs.AI"],
            "published_date": "2023-01-02"
        },
        {
            "id": "2301.00003",
            "arxiv_id": "2301.00003",
            "title": "GPT-4 Technical Report",
            "abstract": "We report the development of GPT-4, a large-scale multimodal model.",
            "authors": ["OpenAI"],
            "categories": ["cs.AI"],
            "published_date": "2023-01-03"
        }
    ]
    
    print(f"\n使用 {len(papers)} 篇测试论文")
    
    # 使用便捷函数
    results = search_papers_bm25(
        query="transformer",
        papers=papers
    )
    
    print(f"\n搜索 'transformer' 的结果:")
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper['title']}")
        if 'search_score' in paper:
            print(f"   Score: {paper['search_score']:.4f}")
    
    print("\n✅ 简单使用测试通过！")
    
    # 清理
    from pathlib import Path
    import shutil
    index_path = Path("./search_index")
    if index_path.exists():
        shutil.rmtree(index_path)


if __name__ == "__main__":
    try:
        # 测试基本功能
        test_search_engine()
        
        # 测试简单使用
        test_simple_usage()
        
        print("\n🎉 所有测试成功！搜索引擎可以正常使用。")
        
    except ImportError as e:
        print("\n❌ 导入错误！")
        print(f"   {e}")
        print("\n请安装 tantivy:")
        print("   pip install tantivy")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
