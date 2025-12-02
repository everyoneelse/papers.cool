#!/usr/bin/env python3
"""
测试短语搜索：对比本地和 arXiv 的短语匹配行为
"""

import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "frontend"))

from search_engine import PaperSearchEngine

# 加载 baseline 数据
with open('validation_output/papers_2025-11-25_baseline.json', 'r') as f:
    data = json.load(f)
    papers = data['papers']

print(f"Loaded {len(papers)} papers\n")
print("="*80)
print("Test: Phrase Search for 'large language model'")
print("="*80)

# 创建搜索引擎
engine = PaperSearchEngine(index_path="./test_phrase_index")
engine.clear_index()
engine.build_index_from_papers(papers)

# 测试 1: AND 模式（所有词出现但不连续）
print("\n1. AND mode (require_all_words=True):")
results_and = engine.search(
    query="large language model",
    max_results=1000,
    require_all_words=True,
    phrase_search=False
)
print(f"   Found: {len(results_and)} papers")

# 测试 2: 短语模式（严格连续）
print("\n2. Phrase mode (phrase_search=True):")
results_phrase = engine.search(
    query="large language model",
    max_results=1000,
    phrase_search=True,
    require_all_words=False
)
print(f"   Found: {len(results_phrase)} papers")

# 分析差异
and_ids = set(r.get('id') or r.get('arxiv_id', '') for r in results_and)
phrase_ids = set(r.get('id') or r.get('arxiv_id', '') for r in results_phrase)

extra_in_and = and_ids - phrase_ids
print(f"\n3. Papers in AND but not in PHRASE: {len(extra_in_and)}")

# 显示几个例子
if extra_in_and:
    print("\n   Examples (papers with all 3 words but not as consecutive phrase):")
    for arxiv_id in list(extra_in_and)[:3]:
        clean_id = arxiv_id.split('v')[0]
        for paper in papers:
            if paper['arxiv_id'].startswith(clean_id):
                title = paper['title']
                abstract = paper['abstract'][:200]
                print(f"\n   ID: {arxiv_id}")
                print(f"   Title: {title}")
                
                # 检查标题和摘要
                has_in_title = 'large language model' in title.lower()
                has_in_abstract = 'large language model' in abstract.lower()
                print(f"   Has phrase in title: {has_in_title}")
                print(f"   Has phrase in abstract (first 200 chars): {has_in_abstract}")
                break

print("\n" + "="*80)
print("Summary:")
print(f"  AND mode: {len(results_and)} papers (all 3 words present)")
print(f"  Phrase mode: {len(results_phrase)} papers (consecutive match)")
print(f"  Difference: {len(extra_in_and)} papers")
print("="*80)

