"""
arXiv Advanced Search Implementation
实现 arXiv 官方高级搜索功能，用于对比本地数据的完整性和准确性
"""

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import time
import logging
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ArxivAdvancedSearch:
    """
    arXiv 官方 Advanced Search API 客户端
    
    使用 arXiv API 进行高级搜索：
    - 支持关键词搜索（标题、摘要）
    - 支持日期范围过滤
    - 支持分类过滤
    - 支持多种搜索字段组合
    """
    
    BASE_URL = "http://export.arxiv.org/api/query"
    MAX_RESULTS_PER_REQUEST = 1000  # arXiv API 单次请求最大结果数
    
    def __init__(self, delay_seconds: float = 3.0):
        """
        初始化搜索客户端
        
        Args:
            delay_seconds: 请求间隔时间（arXiv 要求至少 3 秒）
        """
        self.delay_seconds = max(delay_seconds, 3.0)
        self.last_request_time = 0
    
    def _wait_if_needed(self):
        """遵守 arXiv API 速率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.delay_seconds:
            wait_time = self.delay_seconds - elapsed
            logger.debug(f"Waiting {wait_time:.1f}s to respect rate limit...")
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _build_query(
        self,
        keywords: Optional[str] = None,
        categories: Optional[List[str]] = None,
        search_fields: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> str:
        """
        构建 arXiv API 查询字符串
        
        Args:
            keywords: 搜索关键词
            categories: 分类列表 (e.g., ['cs.AI', 'cs.CV'])
            search_fields: 搜索字段 (e.g., ['ti', 'abs'] for title and abstract)
            
        Returns:
            查询字符串
        """
        query_parts = []
        
        # 构建关键词查询
        if keywords:
            if search_fields is None:
                search_fields = ['ti', 'abs']  # 默认搜索标题和摘要
            
            # 为每个字段构建查询
            field_queries = []
            for field in search_fields:
                field_queries.append(f'{field}:"{keywords}"')
            
            if len(field_queries) == 1:
                query_parts.append(field_queries[0])
            else:
                # 使用 OR 组合多个字段
                query_parts.append(f"({' OR '.join(field_queries)})")
        
        # 构建分类查询
        if categories:
            if len(categories) == 1:
                query_parts.append(f'cat:{categories[0]}')
            else:
                # 使用 OR 组合多个分类
                cat_queries = [f'cat:{cat}' for cat in categories]
                query_parts.append(f"({' OR '.join(cat_queries)})")
        
        # 构建日期查询
        if date_from and date_to:
            start_str = date_from.strftime("%Y%m%d0000")
            end_str = date_to.strftime("%Y%m%d2359")
            query_parts.append(f'submittedDate:[{start_str} TO {end_str}]')
        elif date_from:
            start_str = date_from.strftime("%Y%m%d0000")
            query_parts.append(f'submittedDate:[{start_str} TO 99991231235959]')
        elif date_to:
            end_str = date_to.strftime("%Y%m%d2359")
            query_parts.append(f'submittedDate:[19910101000000 TO {end_str}]')
        
        # 使用 AND 组合所有部分
        if query_parts:
            return ' AND '.join(query_parts)
        else:
            return 'all:*'
    
    def search(
        self,
        keywords: Optional[str] = None,
        categories: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search_fields: Optional[List[str]] = None,
        max_results: int = 1000,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> List[Dict]:
        """
        执行 arXiv advanced search
        
        Args:
            keywords: 搜索关键词
            categories: 分类列表
            date_from: 起始日期
            date_to: 结束日期
            search_fields: 搜索字段列表 ['ti', 'abs', 'au', 'all']
            max_results: 最大结果数
            sort_by: 排序字段 ('relevance', 'lastUpdatedDate', 'submittedDate')
            sort_order: 排序方向 ('ascending', 'descending')
            
        Returns:
            搜索结果列表
        """
        logger.info("=" * 80)
        logger.info("arXiv Advanced Search")
        logger.info(f"Keywords: {keywords}")
        logger.info(f"Categories: {categories}")
        logger.info(f"Date range: {date_from} to {date_to}")
        logger.info("=" * 80)
        
        # 构建查询
        query = self._build_query(keywords, categories, search_fields, date_from, date_to)
        logger.info(f"Query string: {query}")
        
        all_results = []
        start = 0
        batch_size = min(self.MAX_RESULTS_PER_REQUEST, max_results)
        
        while start < max_results:
            # 等待以遵守速率限制
            self._wait_if_needed()
            
            # 构建请求参数
            params = {
                'search_query': query,
                'start': start,
                'max_results': batch_size,
                'sortBy': sort_by,
                'sortOrder': sort_order,
            }
            
            url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
            logger.info(f"Fetching results {start} to {start + batch_size}...")
            
            try:
                # 发送请求
                with urllib.request.urlopen(url) as response:
                    xml_data = response.read()
                
                # 解析 XML
                root = ET.fromstring(xml_data)
                
                # 提取命名空间
                ns = {
                    'atom': 'http://www.w3.org/2005/Atom',
                    'arxiv': 'http://arxiv.org/schemas/atom'
                }
                
                # 解析结果
                entries = root.findall('atom:entry', ns)
                
                if not entries:
                    logger.info("No more results found")
                    break
                
                for entry in entries:
                    paper = self._parse_entry(entry, ns)
                    all_results.append(paper)
                
                # 检查是否已获取所有结果
                total_results = root.find('opensearch:totalResults', {
                    'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'
                })
                
                if total_results is not None:
                    total = int(total_results.text)
                    logger.info(f"Total results available: {total}")
                    if start + len(entries) >= total:
                        break
                
                if len(entries) < batch_size:
                    break
                
                start += batch_size
                
            except Exception as e:
                logger.error(f"Error fetching results: {e}")
                break
        
        logger.info(f"✓ Found {len(all_results)} papers matching criteria")
        return all_results
    
    def _parse_entry(self, entry, ns: Dict) -> Dict:
        """解析单个论文条目"""
        # 提取 ID
        id_elem = entry.find('atom:id', ns)
        arxiv_id = id_elem.text.split('/abs/')[-1] if id_elem is not None else ''
        
        # 提取标题
        title_elem = entry.find('atom:title', ns)
        title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else ''
        
        # 提取摘要
        summary_elem = entry.find('atom:summary', ns)
        abstract = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None else ''
        
        # 提取作者
        authors = []
        for author in entry.findall('atom:author', ns):
            name_elem = author.find('atom:name', ns)
            if name_elem is not None:
                authors.append(name_elem.text)
        
        # 提取分类
        categories = []
        for category in entry.findall('atom:category', ns):
            term = category.get('term')
            if term:
                categories.append(term)
        
        # 提取发布日期
        published_elem = entry.find('atom:published', ns)
        published_date = published_elem.text if published_elem is not None else ''
        
        # 提取更新日期
        updated_elem = entry.find('atom:updated', ns)
        updated_date = updated_elem.text if updated_elem is not None else ''
        
        # 提取 PDF 链接
        pdf_url = ''
        for link in entry.findall('atom:link', ns):
            if link.get('title') == 'pdf':
                pdf_url = link.get('href', '')
                break
        
        return {
            'arxiv_id': arxiv_id,
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'categories': categories,
            'published_date': published_date,
            'updated_date': updated_date,
            'pdf_url': pdf_url,
        }
    
    def search_by_date_and_category(
        self,
        date: datetime,
        categories: Optional[List[str]] = None,
        keywords: Optional[str] = None,
    ) -> Dict[str, List[Dict]]:
        """
        按日期和分类搜索（用于与本地数据对比）
        
        Args:
            date: 目标日期
            categories: 分类列表
            keywords: 可选的关键词过滤
            
        Returns:
            按分类组织的论文字典
        """
        # 设置日期范围（当天）
        date_from = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # 如果没有指定分类，搜索所有
        if categories is None:
            categories = [
                "cs.AI", "cs.CL", "cs.CV", "cs.LG", 
                "cs.NE", "cs.CC", "stat.ML"
            ]
        
        papers_by_category = defaultdict(list)
        
        # 对每个分类分别搜索
        for category in categories:
            logger.info(f"Searching category: {category}")
            
            papers = self.search(
                keywords=keywords,
                categories=[category],
                date_from=date_from,
                date_to=date_to,
                max_results=10000,
                sort_by="submittedDate",
                sort_order="descending",
            )
            
            papers_by_category[category] = papers
            logger.info(f"  → Found {len(papers)} papers in {category}")
        
        return dict(papers_by_category)


def compare_with_local_data(
    arxiv_results: Dict[str, List[Dict]],
    local_papers: Dict[str, List[Dict]],
    date: datetime,
) -> Dict:
    """
    对比 arXiv 官方搜索结果与本地数据
    
    Args:
        arxiv_results: arXiv 官方搜索结果（按分类组织）
        local_papers: 本地论文数据（按分类组织）
        date: 目标日期
        
    Returns:
        对比报告
    """
    report = {
        'date': date.strftime('%Y-%m-%d'),
        'categories': {},
        'summary': {
            'total_arxiv': 0,
            'total_local': 0,
            'total_matched': 0,
            'total_missing_in_local': 0,
            'total_extra_in_local': 0,
        }
    }
    
    all_categories = set(list(arxiv_results.keys()) + list(local_papers.keys()))
    
    for category in all_categories:
        arxiv_papers = arxiv_results.get(category, [])
        local_papers_list = local_papers.get(category, [])
        
        # 提取 ID 集合（移除版本号进行比较）
        arxiv_ids = set()
        for paper in arxiv_papers:
            arxiv_id = paper['arxiv_id'].split('v')[0]
            arxiv_ids.add(arxiv_id)
        
        local_ids = set()
        for paper in local_papers_list:
            arxiv_id = paper.get('arxiv_id', '').split('v')[0]
            if arxiv_id:
                local_ids.add(arxiv_id)
        
        # 计算差异
        matched = arxiv_ids & local_ids
        missing_in_local = arxiv_ids - local_ids
        extra_in_local = local_ids - arxiv_ids
        
        category_report = {
            'arxiv_count': len(arxiv_ids),
            'local_count': len(local_ids),
            'matched_count': len(matched),
            'missing_in_local_count': len(missing_in_local),
            'extra_in_local_count': len(extra_in_local),
            'match_rate': len(matched) / len(arxiv_ids) * 100 if arxiv_ids else 100,
            'missing_ids': sorted(list(missing_in_local)),
            'extra_ids': sorted(list(extra_in_local)),
        }
        
        report['categories'][category] = category_report
        
        # 更新总计
        report['summary']['total_arxiv'] += len(arxiv_ids)
        report['summary']['total_local'] += len(local_ids)
        report['summary']['total_matched'] += len(matched)
        report['summary']['total_missing_in_local'] += len(missing_in_local)
        report['summary']['total_extra_in_local'] += len(extra_in_local)
    
    # 计算总体匹配率
    if report['summary']['total_arxiv'] > 0:
        report['summary']['overall_match_rate'] = (
            report['summary']['total_matched'] / report['summary']['total_arxiv'] * 100
        )
    else:
        report['summary']['overall_match_rate'] = 100
    
    return report


def print_comparison_report(report: Dict):
    """打印对比报告"""
    print("\n" + "=" * 80)
    print(f"arXiv Data Comparison Report - {report['date']}")
    print("=" * 80)
    
    # 总体统计
    summary = report['summary']
    print(f"\n📊 Overall Statistics:")
    print(f"  arXiv Official: {summary['total_arxiv']} papers")
    print(f"  Local Data:     {summary['total_local']} papers")
    print(f"  Matched:        {summary['total_matched']} papers")
    print(f"  Match Rate:     {summary['overall_match_rate']:.2f}%")
    
    if summary['total_missing_in_local'] > 0:
        print(f"  ⚠️  Missing in local: {summary['total_missing_in_local']} papers")
    if summary['total_extra_in_local'] > 0:
        print(f"  ℹ️  Extra in local:   {summary['total_extra_in_local']} papers")
    
    # 分类详情
    print(f"\n📋 By Category:")
    for category, cat_report in sorted(report['categories'].items()):
        print(f"\n  {category}:")
        print(f"    arXiv: {cat_report['arxiv_count']}, Local: {cat_report['local_count']}, "
              f"Matched: {cat_report['matched_count']} ({cat_report['match_rate']:.1f}%)")
        
        if cat_report['missing_in_local_count'] > 0:
            print(f"    ⚠️  Missing in local ({cat_report['missing_in_local_count']}):")
            for arxiv_id in cat_report['missing_ids'][:5]:  # 只显示前 5 个
                print(f"       - {arxiv_id}")
            if cat_report['missing_in_local_count'] > 5:
                print(f"       ... and {cat_report['missing_in_local_count'] - 5} more")
        
        if cat_report['extra_in_local_count'] > 0:
            print(f"    ℹ️  Extra in local ({cat_report['extra_in_local_count']}):")
            for arxiv_id in cat_report['extra_ids'][:5]:
                print(f"       - {arxiv_id}")
            if cat_report['extra_in_local_count'] > 5:
                print(f"       ... and {cat_report['extra_in_local_count'] - 5} more")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="arXiv Advanced Search and Comparison Tool")
    parser.add_argument(
        '--keywords',
        type=str,
        help='Search keywords'
    )
    parser.add_argument(
        '--categories',
        type=str,
        nargs='+',
        help='Categories to search (e.g., cs.AI cs.CV)'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Date to search (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--local-data-dir',
        type=str,
        default='./papers_data',
        help='Local data directory'
    )
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare with local data'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for results (JSON)'
    )
    
    args = parser.parse_args()
    
    # 创建搜索客户端
    searcher = ArxivAdvancedSearch()
    
    # 解析日期
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d')
    else:
        target_date = datetime.now() - timedelta(days=1)
    
    # 执行搜索
    arxiv_results = searcher.search_by_date_and_category(
        date=target_date,
        categories=args.categories,
        keywords=args.keywords,
    )
    
    # 保存结果
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(arxiv_results, f, ensure_ascii=False, indent=2)
        logger.info(f"Results saved to {output_path}")
    
    # 对比本地数据
    if args.compare:
        local_data_dir = Path(args.local_data_dir)
        local_papers = {}
        
        # 加载本地数据
        for category in arxiv_results.keys():
            category_file = local_data_dir / category / f"papers_{target_date.strftime('%Y-%m-%d')}_100percent.json"
            if category_file.exists():
                with open(category_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    local_papers[category] = data.get('papers', [])
                    logger.info(f"Loaded {len(local_papers[category])} papers from {category_file}")
            else:
                logger.warning(f"Local file not found: {category_file}")
                local_papers[category] = []
        
        # 执行对比
        report = compare_with_local_data(arxiv_results, local_papers, target_date)
        
        # 打印报告
        print_comparison_report(report)
        
        # 保存报告
        if args.output:
            report_path = Path(args.output).parent / f"comparison_report_{target_date.strftime('%Y-%m-%d')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"Comparison report saved to {report_path}")

