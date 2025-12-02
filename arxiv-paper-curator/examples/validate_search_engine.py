#!/usr/bin/env python3
"""
验证搜索引擎准确性

流程：
1. 从 arXiv API 获取指定日期+分类的所有论文
2. 用本地 search_engine 搜索关键词 → 结果A
3. 用 arXiv API 直接搜索关键词 → 结果B
4. 对比 A 和 B
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "frontend"))

from src.scripts.arxiv_advanced_search import ArxivAdvancedSearch
from search_engine import PaperSearchEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_all_papers_from_arxiv(date: datetime, categories: list, output_file: Path):
    """
    Step 1: 从 arXiv 获取指定日期和分类的所有论文
    """
    logger.info("="*80)
    logger.info("Step 1: Fetching ALL papers from arXiv API")
    logger.info(f"Date: {date.strftime('%Y-%m-%d')}")
    logger.info(f"Categories: {categories}")
    logger.info("="*80)
    
    searcher = ArxivAdvancedSearch(delay_seconds=3.0)
    
    all_papers = []
    for category in categories:
        logger.info(f"\nFetching category: {category}")
        papers = searcher.search(
            categories=[category],
            date_from=date,
            date_to=date,
            max_results=10000
        )
        
        for paper in papers:
            paper['source_category'] = category
        
        all_papers.extend(papers)
        logger.info(f"  → Found {len(papers)} papers in {category}")
    
    # 保存到文件
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "metadata": {
            "fetch_date": datetime.now().isoformat(),
            "target_date": date.strftime('%Y-%m-%d'),
            "categories": categories,
            "total_papers": len(all_papers),
            "source": "arxiv_api"
        },
        "papers": all_papers
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n✓ Saved {len(all_papers)} papers to {output_file}")
    return all_papers


def search_with_local_engine(papers: list, keywords: str, phrase_search: bool = False, require_all_words: bool = True, remove_stopwords: bool = False):
    """
    Step 2a: 用本地搜索引擎搜索
    """
    logger.info("\n" + "="*80)
    logger.info(f"Step 2a: Searching with LOCAL search engine")
    logger.info(f"Keywords: {keywords}")
    logger.info(f"Phrase search: {phrase_search}")
    logger.info(f"Require all words: {require_all_words}")
    logger.info(f"Remove stopwords: {remove_stopwords}")
    logger.info("="*80)
    
    # 创建搜索引擎并构建索引
    engine = PaperSearchEngine(index_path="./validation_search_index")
    engine.clear_index()
    engine.build_index_from_papers(papers)
    
    # 搜索
    results = engine.search(
        query=keywords, 
        max_results=1000, 
        phrase_search=phrase_search,
        require_all_words=require_all_words,
        remove_stopwords=remove_stopwords
    )
    
    logger.info(f"✓ Local search found {len(results)} papers")
    return results


def search_with_arxiv_api(date: datetime, categories: list, keywords: str):
    """
    Step 2b: 用 arXiv API 搜索
    """
    logger.info("\n" + "="*80)
    logger.info(f"Step 2b: Searching with arXiv API")
    logger.info(f"Keywords: {keywords}")
    logger.info("="*80)
    
    searcher = ArxivAdvancedSearch(delay_seconds=3.0)
    
    all_results = []
    for category in categories:
        logger.info(f"\nSearching category: {category}")
        papers = searcher.search(
            keywords=keywords,
            categories=[category],
            date_from=date,
            date_to=date,
            max_results=10000
        )
        all_results.extend(papers)
        logger.info(f"  → Found {len(papers)} papers in {category}")
    
    logger.info(f"\n✓ arXiv API search found {len(all_results)} papers")
    return all_results


def compare_search_results(local_results: list, arxiv_results: list):
    """
    Step 3: 对比搜索结果
    """
    logger.info("\n" + "="*80)
    logger.info("Step 3: Comparing search results")
    logger.info("="*80)
    
    # 提取ID集合
    local_ids = set()
    for paper in local_results:
        paper_id = paper.get('id') or paper.get('arxiv_id', '')
        clean_id = paper_id.split('v')[0] if paper_id else ''
        if clean_id:
            local_ids.add(clean_id)
    
    arxiv_ids = set()
    for paper in arxiv_results:
        paper_id = paper.get('arxiv_id', '')
        clean_id = paper_id.split('v')[0] if paper_id else ''
        if clean_id:
            arxiv_ids.add(clean_id)
    
    # 对比
    matched = local_ids & arxiv_ids
    missing_in_local = arxiv_ids - local_ids
    extra_in_local = local_ids - arxiv_ids
    
    match_rate = len(matched) / len(arxiv_ids) * 100 if arxiv_ids else 100
    
    # 打印报告
    print("\n" + "="*80)
    print("SEARCH ENGINE VALIDATION REPORT")
    print("="*80)
    print(f"\n📊 Statistics:")
    print(f"  Local Search Results:  {len(local_ids)}")
    print(f"  arXiv API Results:     {len(arxiv_ids)}")
    print(f"  Matched:               {len(matched)}")
    print(f"  Match Rate:            {match_rate:.2f}%")
    
    if missing_in_local:
        print(f"\n⚠️  Missing in Local Search ({len(missing_in_local)}):")
        for arxiv_id in sorted(list(missing_in_local))[:10]:
            print(f"    - {arxiv_id}")
        if len(missing_in_local) > 10:
            print(f"    ... and {len(missing_in_local) - 10} more")
    
    if extra_in_local:
        print(f"\nℹ️  Extra in Local Search ({len(extra_in_local)}):")
        for arxiv_id in sorted(list(extra_in_local))[:10]:
            print(f"    - {arxiv_id}")
        if len(extra_in_local) > 10:
            print(f"    ... and {len(extra_in_local) - 10} more")
    
    if match_rate == 100:
        print(f"\n✅ PERFECT MATCH! Search engine is 100% accurate.")
    elif match_rate >= 95:
        print(f"\n✓ Good match rate. Minor discrepancies detected.")
    else:
        print(f"\n⚠️  Match rate is below 95%. Please check search engine logic.")
    
    print("="*80)
    
    return {
        'local_count': len(local_ids),
        'arxiv_count': len(arxiv_ids),
        'matched': len(matched),
        'match_rate': match_rate,
        'missing_in_local': sorted(list(missing_in_local)),
        'extra_in_local': sorted(list(extra_in_local))
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="验证搜索引擎准确性"
    )
    parser.add_argument(
        '--date',
        type=str,
        required=True,
        help='目标日期 (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--categories',
        type=str,
        nargs='+',
        default=['cs.AI'],
        help='分类列表'
    )
    parser.add_argument(
        '--keywords',
        type=str,
        required=True,
        help='搜索关键词'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='./validation_output',
        help='输出目录'
    )
    parser.add_argument(
        '--skip-fetch',
        action='store_true',
        help='跳过获取步骤，使用已存在的数据文件'
    )
    parser.add_argument(
        '--phrase-search',
        action='store_true',
        help='使用严格短语搜索（连续匹配）'
    )
    parser.add_argument(
        '--require-all-words',
        action='store_true',
        default=True,
        help='要求所有词都出现（默认True，与arXiv一致）'
    )
    parser.add_argument(
        '--no-require-all-words',
        action='store_false',
        dest='require_all_words',
        help='不要求所有词（OR模式）'
    )
    parser.add_argument(
        '--remove-stopwords',
        action='store_true',
        help='移除停用词（a, an, the, in, on, 等）'
    )
    
    args = parser.parse_args()
    
    # 解析日期
    target_date = datetime.strptime(args.date, '%Y-%m-%d')
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 数据文件路径
    papers_file = output_dir / f"papers_{args.date}_baseline.json"
    
    # Step 1: 获取所有论文（或加载已有数据）
    if args.skip_fetch and papers_file.exists():
        logger.info(f"Loading existing data from {papers_file}")
        with open(papers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_papers = data['papers']
        logger.info(f"✓ Loaded {len(all_papers)} papers")
    else:
        all_papers = fetch_all_papers_from_arxiv(
            target_date,
            args.categories,
            papers_file
        )
    
    # Step 2a: 本地搜索引擎搜索
    local_results = search_with_local_engine(
        all_papers, 
        args.keywords, 
        args.phrase_search,
        args.require_all_words,
        args.remove_stopwords
    )
    
    # Step 2b: arXiv API 搜索
    arxiv_results = search_with_arxiv_api(
        target_date,
        args.categories,
        args.keywords
    )
    
    # Step 3: 对比结果
    comparison = compare_search_results(local_results, arxiv_results)
    
    # 保存报告
    report_file = output_dir / f"validation_report_{args.date}.json"
    report_data = {
        "metadata": {
            "validation_date": datetime.now().isoformat(),
            "target_date": args.date,
            "categories": args.categories,
            "keywords": args.keywords,
        },
        "comparison": comparison,
        "local_results": [
            {
                'id': r.get('id') or r.get('arxiv_id', ''),
                'title': r.get('title', ''),
                'search_score': r.get('search_score', 0)
            }
            for r in local_results
        ],
        "arxiv_results": [
            {
                'arxiv_id': r.get('arxiv_id', ''),
                'title': r.get('title', '')
            }
            for r in arxiv_results
        ]
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n💾 Validation report saved to {report_file}")


if __name__ == "__main__":
    main()

