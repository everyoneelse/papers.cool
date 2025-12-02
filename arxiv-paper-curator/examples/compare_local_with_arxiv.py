"""
对比本地数据与 arXiv 官方搜索结果的示例脚本

使用方法:
    python compare_local_with_arxiv.py --date 2024-11-25 --keywords "large language model"
    python compare_local_with_arxiv.py --date 2024-11-25 --categories cs.AI cs.CV
    python compare_local_with_arxiv.py --date 2024-11-25  # 对比所有分类
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scripts.arxiv_advanced_search import (
    ArxivAdvancedSearch,
    compare_with_local_data,
    print_comparison_report
)
from datetime import datetime, timedelta
import json
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_local_papers_by_announced_date(data_dir: Path, date: datetime, categories: list) -> dict:
    """
    按announced date加载本地论文数据
    """
    local_papers = {}
    date_str = date.strftime('%Y-%m-%d')
    
    for category in categories:
        category_file = data_dir / category / f"papers_{date_str}_100percent.json"
        
        if category_file.exists():
            try:
                with open(category_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    papers = data.get('papers', [])
                    local_papers[category] = papers
                    logger.info(f"✓ Loaded {len(papers)} papers from {category}")
            except Exception as e:
                logger.error(f"✗ Error loading {category_file}: {e}")
                local_papers[category] = []
        else:
            logger.warning(f"⚠ File not found: {category_file}")
            local_papers[category] = []
    
    return local_papers


def reorganize_by_submitted_date(papers_by_category: dict, target_submitted_date: datetime) -> dict:
    """
    将按announced date组织的论文重新按submitted date组织
    
    Args:
        papers_by_category: 按category组织的论文
        target_submitted_date: 目标submitted date
        
    Returns:
        按submitted date过滤后的论文字典
    """
    from collections import defaultdict
    
    target_date_str = target_submitted_date.strftime('%Y-%m-%d')
    reorganized = {}
    
    for category, papers in papers_by_category.items():
        reorganized[category] = []
        for paper in papers:
            paper_submitted_date_raw = paper.get('published_date', '')
            try:
                # 将ISO格式日期转换为YYYY-MM-DD格式
                if paper_submitted_date_raw:
                    paper_submitted_date = datetime.fromisoformat(paper_submitted_date_raw.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                else:
                    paper_submitted_date = ''
            except (ValueError, TypeError):
                # 如果解析失败，使用原始值或空字符串
                paper_submitted_date = paper_submitted_date_raw if paper_submitted_date_raw else ''
            #import pdb; pdb.set_trace()
            if paper_submitted_date == target_date_str:
                reorganized[category].append(paper)
        
        logger.info(f"  {category}: {len(reorganized[category])} papers with submitted date {target_date_str}")
    
    return reorganized


def load_local_papers_around_date(data_dir: Path, target_date: datetime, categories: list, days_range: int = 7) -> dict:
    """
    加载目标日期前后几天的announced date数据，用于后续按submitted date重组
    
    Args:
        data_dir: 数据目录
        target_date: 目标日期
        categories: 分类列表
        days_range: 向前向后加载的天数范围
        
    Returns:
        合并后的论文字典（按category组织）
    """
    from datetime import timedelta
    from collections import defaultdict
    
    merged_papers = defaultdict(list)
    seen_ids = defaultdict(set)
    
    for offset in range(-days_range, days_range + 1):
        check_date = target_date + timedelta(days=offset)
        date_papers = load_local_papers_by_announced_date(data_dir, check_date, categories)
        
        for category, papers in date_papers.items():
            for paper in papers:
                paper_id = paper.get('arxiv_id', '')
                if paper_id and paper_id not in seen_ids[category]:
                    merged_papers[category].append(paper)
                    seen_ids[category].add(paper_id)
    
    total = sum(len(papers) for papers in merged_papers.values())
    logger.info(f"✓ Loaded total {total} unique papers from ±{days_range} days around {target_date.strftime('%Y-%m-%d')}")
    
    return dict(merged_papers)


def main():
    parser = argparse.ArgumentParser(
        description="对比本地论文数据与 arXiv 官方搜索结果",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 对比指定日期的所有分类
  python compare_local_with_arxiv.py --date 2024-11-25
  
  # 对比指定日期和分类
  python compare_local_with_arxiv.py --date 2024-11-25 --categories cs.AI cs.CV
  
  # 使用关键词过滤
  python compare_local_with_arxiv.py --date 2024-11-25 --keywords "large language model"
  
  # 保存结果
  python compare_local_with_arxiv.py --date 2024-11-25 --output ./comparison_results
        """
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
        default=['cs.AI', 'cs.CL', 'cs.CV', 'cs.LG', 'cs.NE', 'cs.CC', 'stat.ML'],
        help='要对比的分类列表 (默认: 所有 AI 相关分类)'
    )
    parser.add_argument(
        '--keywords',
        type=str,
        help='可选的关键词过滤'
    )
    parser.add_argument(
        '--local-data-dir',
        type=str,
        default='./papers_data',
        help='本地数据目录 (默认: ./papers_data)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='输出目录（保存对比结果和报告）'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=3.0,
        help='API 请求间隔秒数 (默认: 3.0)'
    )
    parser.add_argument(
        '--by-submitted-date',
        action='store_true',
        help='按 submitted date 对比（默认按 announced date）'
    )
    
    args = parser.parse_args()
    
    # 解析日期
    try:
        target_date = datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
        return
    
    logger.info("=" * 80)
    logger.info("🔍 arXiv Data Comparison Tool")
    logger.info("=" * 80)
    logger.info(f"📅 Date: {target_date.strftime('%Y-%m-%d')}")
    logger.info(f"📅 Date Type: {'submitted date' if args.by_submitted_date else 'announced date'}")
    logger.info(f"📂 Categories: {', '.join(args.categories)}")
    if args.keywords:
        logger.info(f"🔑 Keywords: {args.keywords}")
    logger.info(f"📁 Local data dir: {args.local_data_dir}")
    logger.info("=" * 80)
    
    local_data_dir = Path(args.local_data_dir)
    if not local_data_dir.exists():
        logger.error(f"Local data directory not found: {local_data_dir}")
        return
    
    if args.by_submitted_date:
        # 按submitted date对比模式
        logger.info("\n💾 Step 1: Loading local data around target date...")
        all_local_papers = load_local_papers_around_date(
            local_data_dir, target_date, args.categories, days_range=7
        )
        
        logger.info(f"\n🔄 Step 2: Reorganizing by submitted date {target_date.strftime('%Y-%m-%d')}...")
        local_papers = reorganize_by_submitted_date(all_local_papers, target_date)
        total_local = sum(len(papers) for papers in local_papers.values())
        logger.info(f"✓ Found {total_local} papers with submitted date {target_date.strftime('%Y-%m-%d')}")
        
        logger.info("\n🌐 Step 3: Fetching from arXiv API (by submitted date)...")
        searcher = ArxivAdvancedSearch(delay_seconds=args.delay)
        arxiv_results = searcher.search_by_date_and_category(
            date=target_date,
            categories=args.categories,
            keywords=args.keywords,
        )
        total_arxiv = sum(len(papers) for papers in arxiv_results.values())
        logger.info(f"✓ Retrieved {total_arxiv} papers from arXiv API")
    else:
        # 按announced date对比模式（原有逻辑）
        logger.info("\n💾 Step 1: Loading local data...")
        local_papers = load_local_papers_by_announced_date(local_data_dir, target_date, args.categories)
        total_local = sum(len(papers) for papers in local_papers.values())
        logger.info(f"✓ Loaded {total_local} papers from local storage")
        
        logger.info("\n🌐 Step 2: Fetching from arXiv API...")
        searcher = ArxivAdvancedSearch(delay_seconds=args.delay)
        arxiv_results = searcher.search_by_date_and_category(
            date=target_date,
            categories=args.categories,
            keywords=args.keywords,
        )
        total_arxiv = sum(len(papers) for papers in arxiv_results.values())
        logger.info(f"✓ Retrieved {total_arxiv} papers from arXiv API")
    
    # 3️⃣ 执行对比
    logger.info("\n⚖️  Step 3: Comparing results...")
    report = compare_with_local_data(arxiv_results, local_papers, target_date)
    
    # 4️⃣ 打印报告
    print_comparison_report(report)
    
    # 5️⃣ 保存结果（可选）
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存 arXiv 搜索结果
        arxiv_file = output_dir / f"arxiv_results_{target_date.strftime('%Y-%m-%d')}.json"
        with open(arxiv_file, 'w', encoding='utf-8') as f:
            json.dump(arxiv_results, f, ensure_ascii=False, indent=2)
        logger.info(f"\n💾 Saved arXiv results to: {arxiv_file}")
        
        # 保存对比报告
        report_file = output_dir / f"comparison_report_{target_date.strftime('%Y-%m-%d')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Saved comparison report to: {report_file}")
        
        # 生成详细的 Markdown 报告
        md_file = output_dir / f"comparison_report_{target_date.strftime('%Y-%m-%d')}.md"
        generate_markdown_report(report, arxiv_results, local_papers, md_file)
        logger.info(f"💾 Saved Markdown report to: {md_file}")
    
    # 6️⃣ 显示建议
    print("\n" + "=" * 80)
    print("💡 Recommendations:")
    
    if report['summary']['total_missing_in_local'] > 0:
        print(f"  ⚠️  You have {report['summary']['total_missing_in_local']} papers missing in local storage.")
        print(f"     Consider re-running the fetch script for {target_date.strftime('%Y-%m-%d')}")
    
    if report['summary']['overall_match_rate'] == 100:
        print(f"  ✅ Perfect match! Your local data is 100% complete.")
    elif report['summary']['overall_match_rate'] >= 95:
        print(f"  ✓ Good match rate ({report['summary']['overall_match_rate']:.1f}%). Minor discrepancies detected.")
    else:
        print(f"  ⚠️  Match rate is {report['summary']['overall_match_rate']:.1f}%. Please check your fetch process.")
    
    print("=" * 80)


def generate_markdown_report(report: dict, arxiv_results: dict, local_papers: dict, output_file: Path):
    """生成详细的 Markdown 格式报告"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# arXiv Data Comparison Report\n\n")
        f.write(f"**Date:** {report['date']}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 总体统计
        f.write("## 📊 Overall Statistics\n\n")
        summary = report['summary']
        f.write(f"| Metric | Count |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| arXiv Official | {summary['total_arxiv']} |\n")
        f.write(f"| Local Data | {summary['total_local']} |\n")
        f.write(f"| Matched | {summary['total_matched']} |\n")
        f.write(f"| Match Rate | {summary['overall_match_rate']:.2f}% |\n")
        f.write(f"| Missing in Local | {summary['total_missing_in_local']} |\n")
        f.write(f"| Extra in Local | {summary['total_extra_in_local']} |\n\n")
        
        # 分类详情
        f.write("## 📋 Category Details\n\n")
        
        for category in sorted(report['categories'].keys()):
            cat_report = report['categories'][category]
            
            # 状态图标
            if cat_report['match_rate'] == 100:
                status = "✅"
            elif cat_report['match_rate'] >= 95:
                status = "✓"
            else:
                status = "⚠️"
            
            f.write(f"### {status} {category}\n\n")
            f.write(f"- **arXiv:** {cat_report['arxiv_count']} papers\n")
            f.write(f"- **Local:** {cat_report['local_count']} papers\n")
            f.write(f"- **Matched:** {cat_report['matched_count']} ({cat_report['match_rate']:.1f}%)\n")
            
            # 缺失的论文
            if cat_report['missing_in_local_count'] > 0:
                f.write(f"\n**⚠️ Missing in Local ({cat_report['missing_in_local_count']}):**\n\n")
                for arxiv_id in cat_report['missing_ids']:
                    f.write(f"- [{arxiv_id}](https://arxiv.org/abs/{arxiv_id})\n")
            
            # 额外的论文
            if cat_report['extra_in_local_count'] > 0:
                f.write(f"\n**ℹ️ Extra in Local ({cat_report['extra_in_local_count']}):**\n\n")
                for arxiv_id in cat_report['extra_ids']:
                    f.write(f"- [{arxiv_id}](https://arxiv.org/abs/{arxiv_id})\n")
            
            f.write("\n")
        
        # 建议
        f.write("## 💡 Recommendations\n\n")
        if summary['overall_match_rate'] == 100:
            f.write("✅ **Perfect match!** Your local data is 100% complete.\n")
        elif summary['overall_match_rate'] >= 95:
            f.write(f"✓ **Good match rate** ({summary['overall_match_rate']:.1f}%). Minor discrepancies detected.\n")
        else:
            f.write(f"⚠️ **Match rate is {summary['overall_match_rate']:.1f}%**. Please check your fetch process.\n")
        
        if summary['total_missing_in_local'] > 0:
            f.write(f"\n⚠️ You have **{summary['total_missing_in_local']} papers missing** in local storage. ")
            f.write(f"Consider re-running the fetch script for {report['date']}.\n")


if __name__ == "__main__":
    main()

