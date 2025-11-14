#!/usr/bin/env python3
"""
测试简化版 BM25 搜索引擎
"""
import json
from pathlib import Path

def test_simple_search():
    """测试简化版搜索引擎"""
    
    print("=" * 60)
    print("测试简化版 BM25 搜索引擎")
    print("=" * 60)
    
    # 1. 导入模块
    print("\n1. 导入搜索引擎模块...")
    try:
        from search_engine_simple import SimplePaperSearchEngine, simple_search_papers
        print("   ✅ 导入成功")
    except ImportError as e:
        print(f"   ❌ 导入失败: {e}")
        print("\n请安装 tantivy:")
        print("   pip install tantivy")
        return False
    
    # 2. 创建测试数据
    print("\n2. 创建测试数据...")
    test_papers = [
        {
            "id": "2301.00001",
            "arxiv_id": "2301.00001",
            "title": "Attention Is All You Need: The Transformer Architecture",
            "abstract": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "categories": ["cs.AI", "cs.LG"],
            "published_date": "2023-01-01"
        },
        {
            "id": "2301.00002",
            "arxiv_id": "2301.00002",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "abstract": "We introduce BERT, which stands for Bidirectional Encoder Representations from Transformers.",
            "authors": ["Jacob Devlin", "Ming-Wei Chang"],
            "categories": ["cs.CL", "cs.AI"],
            "published_date": "2023-01-02"
        },
        {
            "id": "2301.00003",
            "arxiv_id": "2301.00003",
            "title": "Large Language Models: GPT-4 Technical Report",
            "abstract": "We report the development of GPT-4, a large-scale multimodal model.",
            "authors": ["OpenAI Team"],
            "categories": ["cs.AI"],
            "published_date": "2023-01-03"
        },
        {
            "id": "2301.00004",
            "arxiv_id": "2301.00004",
            "title": "Vision Transformers for Image Recognition",
            "abstract": "We show that a pure transformer applied directly to image patches can perform very well on image classification.",
            "authors": ["Alexey Dosovitskiy"],
            "categories": ["cs.CV", "cs.LG"],
            "published_date": "2023-01-04"
        }
    ]
    
    print(f"   创建了 {len(test_papers)} 篇测试论文")
    
    # 3. 初始化搜索引擎
    print("\n3. 初始化搜索引擎...")
    try:
        engine = SimplePaperSearchEngine(index_path="./test_simple_index")
        print("   ✅ 初始化成功")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        return False
    
    # 4. 构建索引
    print("\n4. 构建索引...")
    try:
        engine.build_index(test_papers)
        stats = engine.get_index_stats()
        print(f"   ✅ 索引构建成功")
        print(f"   索引状态: {stats}")
    except Exception as e:
        print(f"   ❌ 索引构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 测试搜索
    print("\n5. 测试搜索...")
    
    test_queries = [
        ("transformer", 3),
        ("LLM", 2),
        ("GPT", 1),
        ("vision", 1),
    ]
    
    all_passed = True
    for query, expected_min in test_queries:
        print(f"\n   查询: '{query}'")
        try:
            results = engine.search(query, max_results=10)
            
            if results:
                print(f"   ✅ 找到 {len(results)} 个结果")
                for i, result in enumerate(results[:2], 1):
                    title = result['title'][:60] + "..." if len(result['title']) > 60 else result['title']
                    print(f"      {i}. {title}")
                    print(f"         Score: {result['search_score']:.4f}")
                
                if len(results) < expected_min:
                    print(f"   ⚠️ 预期至少 {expected_min} 个结果，实际 {len(results)} 个")
            else:
                print(f"   ⚠️ 未找到结果")
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ 搜索失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # 6. 测试便捷函数
    print("\n6. 测试便捷函数...")
    try:
        results = simple_search_papers(
            query="transformer",
            papers=test_papers,
            search_engine=engine
        )
        print(f"   ✅ simple_search_papers 返回 {len(results)} 个结果")
    except Exception as e:
        print(f"   ❌ 便捷函数失败: {e}")
        all_passed = False
    
    # 7. 清理
    print("\n7. 清理测试索引...")
    try:
        engine.clear_index()
        print("   ✅ 清理完成")
    except Exception as e:
        print(f"   ⚠️ 清理失败: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        print("=" * 60)
        return True
    else:
        print("⚠️ 部分测试失败")
        print("=" * 60)
        return False


def test_with_real_data():
    """使用真实数据测试"""
    
    print("\n" + "=" * 60)
    print("使用真实论文数据测试")
    print("=" * 60)
    
    # 查找论文数据文件
    data_dir = Path("papers_data")
    if not data_dir.exists():
        print("❌ papers_data 目录不存在")
        return False
    
    json_files = list(data_dir.glob("papers_*.json"))
    if not json_files:
        print("❌ 未找到论文数据文件")
        return False
    
    json_file = sorted(json_files)[-1]
    print(f"\n使用文件: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        papers = data
    elif isinstance(data, dict) and 'papers' in data:
        papers = data['papers']
    else:
        print("❌ 无法解析论文数据")
        return False
    
    print(f"加载了 {len(papers)} 篇论文")
    
    # 导入并测试
    try:
        from search_engine_simple import simple_search_papers
        
        print("\n测试搜索...")
        results = simple_search_papers(
            query="transformer",
            papers=papers[:100]  # 只用前100篇测试
        )
        
        print(f"✅ 找到 {len(results)} 个结果")
        for i, paper in enumerate(results[:3], 1):
            print(f"{i}. {paper['title'][:70]}...")
            if 'search_score' in paper:
                print(f"   Score: {paper['search_score']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 基本测试
    success = test_simple_search()
    
    # 如果基本测试通过，尝试真实数据
    if success:
        test_with_real_data()
    
    print("\n🎉 测试完成！")
