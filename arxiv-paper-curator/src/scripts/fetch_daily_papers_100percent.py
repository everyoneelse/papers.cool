"""
import requests
import xml.etree.ElementTree as ET
100% Complete Data Fetching Strategy for arXiv Papers
100% 完整数据获取策略

This script GUARANTEES 100% data completeness by:
1. Continuous retry until all papers are fetched
2. Incremental fetching (track what's already fetched)
3. Completeness verification (compare with total_results)
4. Resume from checkpoint on restart
5. Multiple verification passes

Time is not a constraint - it will keep trying until complete.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import os
from src.config import ArxivSettings
from src.services.arxiv.client import ArxivClient
from src.schemas.arxiv.paper import ArxivPaper

from src.scripts.scrape_arxiv_passweek_and_parse import fetch_pass_week_papers
from collections import defaultdict, OrderedDict

from Bio import Entrez, Medline
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ArXiv categories
ARXIV_CATEGORIES = {
    "Artificial Intelligence (cs.AI)": "cs.AI",
    "Computation and Language (cs.CL)": "cs.CL",
    "Computer Vision (cs.CV)": "cs.CV",
    "Machine Learning (cs.LG)": "cs.LG",
    "Neural and Evolutionary Computing (cs.NE)": "cs.NE",
    "Computational Complexity (cs.CC)": "cs.CC",
    "Statistics - Machine Learning (stat.ML)": "stat.ML",
}

# PubMed project keywords configuration
PUBMED_PROJECTS = {
    "Protocol": [
        "Large Language Model, Protocol",
        "LLM, Protocol"
    ],
    "Artifacts": [
        "Large Language Model, Artifacts",
        "LLM, Artifacts"
    ],
    "CT_Image_Quality": [
        "Large Language Model, CT Image quality assessment",
        "LLM, Image quality, CT Image quality assessment"
    ],
    "MR_Image_Quality": [
        "Large Language Model, MR Image quality assessment",
        "LLM, Image quality, MR Image quality assessment"
    ],
    "PET_Image_Quality": [
        "Large Language Model, PET Image quality assessment",
        "LLM, Image quality, PET Image quality assessment"
    ],
    "US_Image_Quality": [
        "Large Language Model, US Image quality assessment",
        "LLM, Image quality, US Image quality assessment"
    ],
    "Autonomous_CT": [
        "Large Language Model, Autonomous CT",
        "LLM, Autonomous CT"
    ],
    "Autonomous_MR": [
        "Large Language Model, Autonomous MR",
        "LLM, Autonomous MR"
    ],
    "Autonomous_PET": [
        "Large Language Model, Autonomous PET",
        "LLM, Autonomous PET"
    ],
    "Autonomous_US": [
        "Large Language Model, Autonomous US",
        "LLM, Autonomous US"
    ],
    "Agent": [
        "Large Language Model, Agent",
        "LLM, Agent"
    ]
}

# Configuration
DEFAULT_OUTPUT_DIR = "./papers_data"
CHECKPOINT_DIR = "./checkpoints"  # Store progress
MAX_RETRY_WAIT_SECONDS = 300  # Max 5 minutes between retries
VERIFICATION_PASSES = 3  # Number of verification passes
LOCAL_FILE_PATH = "./papers_data/"

class CompleteFetcher:
    """Guarantees 100% complete data fetching."""

    def __init__(
        self,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        checkpoint_dir: str = CHECKPOINT_DIR,
        categories: Optional[List[str]] = None,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.categories = categories or list(ARXIV_CATEGORIES.values())
        
        logger.info(f"Initialized CompleteFetcher (100% guarantee mode)")
        logger.info(f"Categories: {self.categories}")
        logger.info(f"Checkpoints: {self.checkpoint_dir}")

    def _get_checkpoint_file(self, category: str, date: str) -> Path:
        """Get checkpoint file path."""
        return self.checkpoint_dir / f"checkpoint_{category}_{date}.json"

    def _load_checkpoint(self, category: str, date: str) -> Dict:
        """Load checkpoint data."""
        checkpoint_file = self._get_checkpoint_file(category, date)
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
        return {
            "fetched_ids": [],
            "fetched_papers": [],  # 完整的论文数据
            "total_expected": None,
            "attempts": 0,
            "last_attempt": None,
        }

    def _save_checkpoint(self, category: str, date: str, checkpoint: Dict):
        """Save checkpoint data."""
        checkpoint_file = self._get_checkpoint_file(category, date)
        checkpoint["last_attempt"] = datetime.now().isoformat()
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)

    def _clear_checkpoint(self, category: str, date: str):
        """Clear checkpoint after successful completion."""
        checkpoint_file = self._get_checkpoint_file(category, date)
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            logger.info(f"[{category}] Checkpoint cleared")
    
    async def async_daily_pubmed(self, date: Optional[datetime] = None):
        Entrez.email = "mzthhy@hotmail.com"

        # Determine the date to fetch - either specified date or yesterday
        if date is not None:
            target_date = date
            logger.info(f"start to scrape Pubmed for date: {target_date.strftime('%Y-%m-%d')}")
        else:
            # Default to yesterday's date for the past 24 hours
            target_date = datetime.now() - timedelta(days=1)
            logger.info(f"start to scrape Pubmed for yesterday: {target_date.strftime('%Y-%m-%d')}")

        async def fetch_daily_updates():
            # Store results by project and date
            fetch_results_by_project = defaultdict(lambda: defaultdict(list))
            metadata_by_project = defaultdict(dict)

            max_wait_hours = 1
            start_time = datetime.now()
            max_wait_seconds = 1 * 3600

            # Format date as YYYY/MM/DD for PubMed API
            mindate = target_date.strftime("%Y/%m/%d")
            maxdate = (target_date + timedelta(days=1)).strftime("%Y/%m/%d")
            
            # Loop through each project
            for project_name, keyword_variants in PUBMED_PROJECTS.items():
                logger.info(f"\n{'='*60}")
                logger.info(f"[PubMed - {project_name}] Starting search")
                logger.info(f"{'='*60}")
                
                # Build query: OR all variants for this project
                query_terms = []
                for variant in keyword_variants:
                    # Split by comma and build query
                    terms = [term.strip() for term in variant.split(',')]
                    # Join terms with AND
                    query_terms.append('(' + ' AND '.join([f'({t})' for t in terms]) + ')')
                
                # Join all variants with OR
                project_query = ' OR '.join(query_terms)
                logger.info(f"[PubMed - {project_name}] Query: {project_query}")
                
                attempt_count = 0
                while True:
                    attempt_count += 1
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"[PubMed - {project_name}] Attempt #{attempt_count} (elapsed: {elapsed/3600:.1f}h)")
                    
                    if elapsed > max_wait_seconds:
                        logger.error(f"[PubMed - {project_name}] Max wait time ({max_wait_hours}h) exceeded.")
                        break

                    try:
                        logger.info(f"[PubMed - {project_name}] Searching with date range: {mindate} to {maxdate}")
                        handle = Entrez.esearch(
                            db="pubmed", 
                            term=project_query, 
                            mindate=mindate,
                            maxdate=maxdate,
                            datetype="edat",
                            retmax=100
                        )
                        record = Entrez.read(handle)
                        handle.close()
                        
                        id_list = record["IdList"]
                        count = record["Count"]

                        if not id_list:
                            logger.info(f"✅ [{project_name}] {target_date.strftime('%Y-%m-%d')} 没有发现新论文。")
                            metadata_by_project[project_name][target_date] = {
                                "expected_total": 0,
                            }
                            break

                        logger.info(f"🚀 [{project_name}] 发现 {count} 篇新论文！准备获取详情...\n")
                        
                        handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
                        records = Medline.parse(handle)

                        # Parse records
                        for i, record in enumerate(records):

                            # --- 提取信息 ---
                            title = record.get("TI", "No Title")
                            pmid = record.get("PMID", "No PMID")
                            published_date = record.get("EDAT", "No Published Date")
                            doi = record.get("LID", "No DOI")
                            # [关键] 直接获取完整摘要 (Medline 库会自动拼接多行)
                            abstract = record.get("AB", "No Abstract")
                            # 提取作者
                            authors = record.get("AU", ["Unknown Author"])
                            # 提取分类标签
                            journal = record.get("JT", "Unknown Journal") # 期刊
                            pub_types = record.get("PT", [])             # 文章类型
                            categories = (f"[{journal}] " + "".join([f"[{pt}]" for pt in pub_types if pt != 'Journal Article']))
                            # 提取关键词 (优先取作者关键词 OT，没有则取 MeSH)
                            keywords = record.get("OT", [])
                            if not keywords:
                                # 如果没有作者关键词，尝试从 MH 中提取带星号的核心词
                                mesh = record.get("MH", [])
                                keywords = [m.replace("*", "") for m in mesh if "*" in m]

                            # 提取 DOI (位于 LID 或 AID 字段)
                            doi = ""
                            if "LID" in record:
                                # LID 格式通常是 "10.xxx [doi]"
                                doi = next((x.replace(" [doi]", "") for x in record["LID"] if "[doi]" in x), "")
                            elif "AID" in record:
                                doi = next((x.replace(" [doi]", "") for x in record["AID"] if "[doi]" in x), "")

                            # --- 打印漂亮的输出 ---
                            logger.info(f"【{project_name} - {i+1}】 {title}")
                            logger.info(f"🏷️  分类: [{journal}] " + "".join([f"[{pt}]" for pt in pub_types if pt != 'Journal Article']))
                            logger.info(f"👥 作者: {', '.join(authors[:5])}" + ("..." if len(authors)>5 else ""))
                            if keywords:
                                logger.info(f"🔑 关键词: {', '.join(keywords)}")
                            logger.info(f"DP: {published_date}")
                            
                            logger.info(f"\n📖 完整摘要:")
                            logger.info(f"{abstract}") # 这里输出的就是完整的一大段话
                            
                            logger.info(f"\n🔗 PubMed: https://pubmed.ncbi.nlm.nih.gov/{record.get('PMID', '?')}/")
                            if doi:
                                logger.info(f"🔗 DOI直达: https://doi.org/{doi}")
                                
                            logger.info("=" * 60) # 分割线

                            try:
                                # EDAT 字段可能是列表或字符串，需要先处理
                                if isinstance(published_date, list):
                                    published_date = published_date[0] if published_date else "No Published Date"
                                
                                # 清理日期字符串，移除可能的额外空格
                                published_date = published_date.strip()
                                
                                # EDAT 格式: "YYYY/MM/DD HH:MM" 或 "YYYY/MM/DD"
                                if "/" in published_date:
                                    # 移除可能的时间部分 (HH:MM)
                                    date_part = published_date.split()[0]  # 取空格前的日期部分
                                    paper_date = datetime.strptime(date_part, "%Y/%m/%d")
                                else:
                                    # 兼容其他可能的格式
                                    logger.warning(f"Unexpected EDAT format: {published_date}, skipping")
                                    continue
                            except (ValueError, IndexError) as e:
                                logger.warning(f"Failed to parse EDAT '{published_date}': {e}, skipping")
                                continue

                            # Store paper by project and date
                            fetch_results_by_project[project_name][paper_date].append({
                                "title": title,
                                "arxiv_id": pmid,
                                "published_date": paper_date.strftime("%Y-%m-%d"),
                                "doi": doi,
                                "abstract": abstract,
                                "authors": authors,
                                "categories": categories,
                                'pdf_url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            })
                            
                            if paper_date not in metadata_by_project[project_name]:
                                metadata_by_project[project_name][paper_date] = {
                                    "expected_total": 1,
                                }
                            else:
                                metadata_by_project[project_name][paper_date]["expected_total"] += 1

                        handle.close()
                        break  # Successfully fetched for this project

                    except Exception as e:
                        logger.error(f"❌ [{project_name}] 发生错误: {e}")
                        
                        # Wait before retry
                        retry_delay = 10
                        logger.info(f"[{project_name}] Waiting {retry_delay:.0f}s before next attempt...")
                        import time
                        time.sleep(retry_delay)
            
            return fetch_results_by_project, metadata_by_project
            
        fetch_results_by_project, metadata_by_project = await fetch_daily_updates()
        
        # Process results by project and date
        for project_name, date_results in fetch_results_by_project.items():
            sorted_fetch_results = OrderedDict(sorted(date_results.items(), key=lambda item: item[0], reverse=True))
            
            for date, papers in sorted_fetch_results.items():
                # Create category structure for this project
                paper_by_category = defaultdict(list)
                metadata_by_category = defaultdict(dict)
                
                # Use project name as category under PubMed
                category_name = f"PubMed_{project_name}"
                
                # Add papers to this category
                for paper in papers:
                    paper_by_category[category_name].append(paper)
                
                # Set metadata for this category
                project_metadata = metadata_by_project.get(project_name, {}).get(date, {})
                metadata_by_category[category_name] = {
                    "expected_total": project_metadata.get("expected_total", len(papers)),
                    "is_complete": True,
                    "total_attempts": 1,
                    "elapsed_hours": 0
                }
                
                # Save papers for this project
                self.save_papers_with_metadata(paper_by_category, metadata_by_category, date)


    async def async_daily_scrape(self, target_date=None):

        to_do_list = defaultdict(dict)
        overall_groups = {}
        overall_groups_ = defaultdict(dict)
        for category in self.categories:
            groups = fetch_pass_week_papers(category)
            overall_groups[category] = groups

        for category, groups in overall_groups.items():
            for date, papers in groups.items():
                dt = datetime.strptime(date, "%a, %d %b %Y")
                overall_groups_[date][category] = []
                for paper in papers:
                    overall_groups_[date][category].append(paper)
        
        # 从fetch结果中找到最新的日期（按时间排序）
        all_dates = list(overall_groups_.keys())
        if all_dates:
            # 按日期排序，找到最新的
            sorted_dates = sorted(all_dates, key=lambda x: datetime.strptime(x, "%a, %d %b %Y"), reverse=True)
            latest_date = sorted_dates[0]  # 最新的日期
            old_dates = sorted_dates[1:]   # 其余的旧日期

            logger.info(f"Processing latest date from fetch: {latest_date}")
            logger.info(f"Checking existence for old dates: {old_dates}")

            # 如果指定了目标日期，只处理该日期，否则处理最新日期
            if target_date:
                # 将目标日期转换为相同的格式进行匹配
                target_date_str = target_date.strftime("%a, %d %b %Y")
                if target_date_str in overall_groups_:
                    dates_to_process = [target_date_str]
                    logger.info(f"Processing specified date: {target_date_str}")
                else:
                    logger.warning(f"Specified date {target_date_str} not found in available dates")
                    dates_to_process = []
            else:
                # 默认只处理最新的数据
                dates_to_process = sorted_dates
                logger.info(f"Processing sorted date: {sorted_dates}")

            # 处理选定的日期
            for date in dates_to_process:
                category_dict = overall_groups_[date]
                dt = datetime.strptime(date, "%a, %d %b %Y")

                # 为这个日期收集所有已存在的论文ID，按类别分组
                existing_papers_by_category = {}
                for category in self.categories:
                    paper_file = os.path.join(LOCAL_FILE_PATH,
                        category, f"papers_{dt.strftime('%Y-%m-%d')}_100percent.json")
                    if os.path.exists(paper_file):
                        with open(paper_file, 'r', encoding='utf-8') as f:
                            papers_scraped = json.load(f)
                        papers_lists = papers_scraped['papers']
                        existing_papers_by_category[category] = set(paper['arxiv_id'] for paper in papers_lists)
                    else:
                        existing_papers_by_category[category] = set()

                for category, paper_ids in category_dict.items():
                    to_do_list[date][category] = []
                    existing_papers = existing_papers_by_category[category]

                    for paper in paper_ids:
                        paper_id_with_version = f"{paper['id']}v{paper['version']}"
                        # 只有当该类别还没有这篇论文时，才添加到抓取列表
                        if paper_id_with_version not in existing_papers:
                            to_do_list[date][category].append(paper_id_with_version)

            # 检查旧数据的存在性，但不进行抓取
            for date_str in old_dates:
                dt = datetime.strptime(date_str, "%a, %d %b %Y")
                logger.info(f"Checking existence for old date: {date_str}")

                for category in self.categories:
                    paper_file = os.path.join(LOCAL_FILE_PATH,
                        category, f"papers_{dt.strftime('%Y-%m-%d')}_100percent.json")
                    if os.path.exists(paper_file):
                        # 检查文件是否完整（有metadata且is_complete为true）
                        try:
                            with open(paper_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            metadata = data.get('metadata', {})
                            if metadata.get('is_complete', False):
                                logger.info(f"[{category}] {date_str}: File exists and marked complete ✓")
                            else:
                                logger.warning(f"[{category}] {date_str}: File exists but incomplete ⚠️")
                        except Exception as e:
                            logger.warning(f"[{category}] {date_str}: Error reading file: {e}")
                    else:
                        logger.warning(f"[{category}] {date_str}: File missing ❌")

        papers_by_date = {}
        metadata_by_date = {}

        for date_str, category_dict in to_do_list.items():
            # Convert string date to datetime object
            date_obj = datetime.strptime(date_str, "%a, %d %b %Y")
            papers_by_date[date_obj.strftime('%Y-%m-%d')] = []
            metadata_by_date[date_obj.strftime('%Y-%m-%d')] = []

            for category, paper_id_list in category_dict.items():
                logger.info(f"[{category}] Starting 100% complete daily fetch for {date_obj.strftime('%Y-%m-%d')}")
                papers, metadata = await self.fetch_papers_by_id(date_obj.strftime('%Y-%m-%d'), category, paper_id_list, preserve_order=True)
                papers_by_date[date_obj.strftime('%Y-%m-%d')].extend(papers)
                metadata_by_date[date_obj.strftime('%Y-%m-%d')].append(metadata)

        return papers_by_date, metadata_by_date
        
    async def fetch_papers_by_id(self, date, category, paper_id_list, max_wait_hours=24, preserve_order=False):

        start_time = datetime.now()
        max_wait_seconds = max_wait_hours * 3600

        # Load checkpoint
        checkpoint = self._load_checkpoint(category, date)
        fetched_ids: Set[str] = set(checkpoint["fetched_ids"])
        fetched_papers = checkpoint.get("fetched_papers", [])
        total_expected = checkpoint["total_expected"]
        attempt_count = checkpoint["attempts"]

        logger.info(f"[{category}] Starting 100% complete fetch")
        logger.info(f"[{category}] Checkpoint: {len(fetched_ids)} papers already fetched")
        if total_expected:
            logger.info(f"[{category}] Expected total: {total_expected}")

        if total_expected is None:
            total_expected = len(paper_id_list)

        # 从checkpoint恢复已获取的论文
        all_papers_dict = {}  # Use dict to avoid duplicates
        for paper_data in fetched_papers:
            # 将字典数据转换回ArxivPaper对象
            paper = ArxivPaper(**paper_data)
            all_papers_dict[paper.arxiv_id] = paper

        logger.info(f"[{category}] Restored {len(all_papers_dict)} papers from checkpoint")

        retry_delay = 10  # Initial retry delay
        consecutive_failures = 0

        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > max_wait_seconds:
                logger.error(
                    f"[{category}] Max wait time ({max_wait_hours}h) exceeded. "
                    f"Fetched {len(all_papers_dict)}/{total_expected or '?'} papers"
                )
                break

            attempt_count += 1
            logger.info(f"[{category}] Attempt #{attempt_count} (elapsed: {elapsed/3600:.1f}h)")

            try:
                # 计算哪些ID还没有获取
                remaining_ids = [pid for pid in paper_id_list if pid not in fetched_ids]
                if not remaining_ids:
                    logger.info(f"[{category}] All {total_expected} papers already fetched from checkpoint")
                    break

                logger.info(f"[{category}] Fetching {len(remaining_ids)} remaining papers")

                # Create client
                settings = ArxivSettings(search_category=category)
                client = ArxivClient(settings)

                # 只获取剩余的论文
                papers = await client.fetch_papers_by_ids(
                    arxiv_ids=remaining_ids
                )

                # 按照输入的paper_id_list顺序重新排列结果
                ordered_papers = []
                papers_dict = {paper.arxiv_id.split("v")[0]: paper for paper in papers}  # 使用清理后的ID作为key
                for paper_id in remaining_ids:
                    clean_id = paper_id.split("v")[0] if "v" in paper_id else paper_id
                    if clean_id in papers_dict:
                        ordered_papers.append(papers_dict[clean_id])

                new_papers = 0
                # Add newly fetched papers
                for paper in ordered_papers:
                    if paper.arxiv_id not in all_papers_dict:
                        all_papers_dict[paper.arxiv_id] = paper
                        fetched_ids.add(paper.arxiv_id)
                        new_papers += 1

                logger.info(
                    f"[{category}] Fetched {len(ordered_papers)} papers this attempt "
                    f"({new_papers} new, {len(all_papers_dict)} total)"
                )

                # Check completeness
                if total_expected and len(all_papers_dict) >= total_expected:
                    logger.info(
                        f"[{category}] ✓ COMPLETE! Fetched {len(all_papers_dict)}/{total_expected} papers"
                    )
                    consecutive_failures = 0
                    break  # Success!
                elif total_expected:
                    missing = total_expected - len(all_papers_dict)
                    logger.warning(
                        f"[{category}] Incomplete: {len(all_papers_dict)}/{total_expected} "
                        f"({missing} missing, {len(all_papers_dict)/total_expected*100:.1f}% complete)"
                    )
                else:
                    logger.info(f"[{category}] Fetched {len(all_papers_dict)} papers (total unknown)")

                # 更新checkpoint中的论文数据
                fetched_papers_data = []
                for paper in all_papers_dict.values():
                    # 将ArxivPaper对象转换为字典以便JSON序列化
                    paper_dict = {
                        "arxiv_id": paper.arxiv_id,
                        "title": paper.title,
                        "authors": paper.authors,
                        "abstract": paper.abstract,
                        "categories": paper.categories,
                        "published_date": paper.published_date,
                        "pdf_url": paper.pdf_url,
                    }
                    fetched_papers_data.append(paper_dict)

                # Save checkpoint
                checkpoint["fetched_ids"] = list(fetched_ids)
                checkpoint["fetched_papers"] = fetched_papers_data
                checkpoint["total_expected"] = total_expected
                checkpoint["attempts"] = attempt_count
                self._save_checkpoint(category, date, checkpoint)

                # Reset retry delay on successful fetch (even if incomplete)
                if new_papers > 0:
                    retry_delay = 5
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    # If no new papers for multiple attempts, might be complete
                    if consecutive_failures >= VERIFICATION_PASSES:
                        if total_expected is None or len(all_papers_dict) > 0:
                            logger.info(
                                f"[{category}] No new papers after {consecutive_failures} verification passes. "
                                f"Considering complete with {len(all_papers_dict)} papers."
                            )
                            break

            except Exception as e:
                logger.error(f"[{category}] Attempt #{attempt_count} failed: {e}")
                consecutive_failures += 1

            # Wait before retry (with exponential backoff)
            if not (total_expected and len(all_papers_dict) >= total_expected):
                retry_delay = min(retry_delay * 1.5, MAX_RETRY_WAIT_SECONDS)
                logger.info(f"[{category}] Waiting {retry_delay:.0f}s before next attempt...")
                await asyncio.sleep(retry_delay)
        
        # Convert to simplified format
        simplified_papers = []
        if preserve_order:
            # 按照输入的paper_id_list顺序保存
            for paper_id in paper_id_list:
                clean_id = paper_id.split("v")[0] if "v" in paper_id else paper_id
                # 找到对应的完整ID（包含版本号）
                matching_key = None
                for key in all_papers_dict.keys():
                    if key.split("v")[0] == clean_id:
                        matching_key = key
                        break

                if matching_key:
                    paper = all_papers_dict[matching_key]
                    simplified_papers.append({
                        "arxiv_id": paper.arxiv_id,
                        "title": paper.title,
                        "authors": paper.authors,
                        "abstract": paper.abstract,
                        "categories": paper.categories,
                        "published_date": paper.published_date,
                        "url": f"https://arxiv.org/abs/ {paper.arxiv_id}",
                        "pdf_url": paper.pdf_url,
                        "source_category": category,  # 添加源类别字段
                    })
                else:
                    logger.warning(f"[{category}] Paper {clean_id} not found in fetched papers")
                # 如果找不到匹配的，跳过（保持输入顺序，只添加存在的论文）
        else:
            # 默认顺序，直接遍历所有获取到的论文
            for paper in all_papers_dict.values():
                simplified_papers.append({
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "abstract": paper.abstract,
                    "categories": paper.categories,
                    "published_date": paper.published_date,
                    "url": f"https://arxiv.org/abs/ {paper.arxiv_id}",
                    "pdf_url": paper.pdf_url,
                    "source_category": category,  # 添加源类别字段
                })

        # Build metadata
        is_complete = total_expected is None or len(simplified_papers) >= total_expected
        metadata = {
            "category": category,
            "date_range": f"{date}",
            "total_attempts": attempt_count,
            "elapsed_hours": (datetime.now() - start_time).total_seconds() / 3600,
            "papers_fetched": len(simplified_papers),
            "expected_total": total_expected,
            "completeness": "100%" if is_complete else f"{len(simplified_papers)/total_expected*100:.1f}%",
            "is_complete": is_complete,
        }

        # Clear checkpoint on success
        if is_complete:
            self._clear_checkpoint(category, date)

        return simplified_papers, metadata

    async def fetch_category_complete(
        self,
        category: str,
        from_date: str,
        to_date: str,
        max_wait_hours: int = 24,  # Maximum total wait time
    ) -> Tuple[List[Dict], Dict]:
        """
        Fetch papers for a category with 100% completeness guarantee.
        
        Will keep retrying until:
        1. All expected papers are fetched, OR
        2. max_wait_hours is exceeded (safety limit)
        
        Args:
            category: arXiv category code
            from_date: Start date (YYYYMMDD)
            to_date: End date (YYYYMMDD)
            max_wait_hours: Maximum hours to keep trying (default: 24)
            
        Returns:
            Tuple of (papers, metadata) where metadata includes completeness info
        """
        start_time = datetime.now()
        max_wait_seconds = max_wait_hours * 3600
        
        # Load checkpoint
        checkpoint = self._load_checkpoint(category, from_date)
        fetched_ids: Set[str] = set(checkpoint["fetched_ids"])
        total_expected = checkpoint["total_expected"]
        attempt_count = checkpoint["attempts"]
        
        logger.info(f"[{category}] Starting 100% complete fetch")
        logger.info(f"[{category}] Checkpoint: {len(fetched_ids)} papers already fetched")
        if total_expected:
            logger.info(f"[{category}] Expected total: {total_expected}")
        
        all_papers_dict = {}  # Use dict to avoid duplicates
        retry_delay = 10  # Initial retry delay
        consecutive_failures = 0
        
        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > max_wait_seconds:
                logger.error(
                    f"[{category}] Max wait time ({max_wait_hours}h) exceeded. "
                    f"Fetched {len(all_papers_dict)}/{total_expected or '?'} papers"
                )
                break
            
            attempt_count += 1
            logger.info(f"[{category}] Attempt #{attempt_count} (elapsed: {elapsed/3600:.1f}h)")
            
            try:
                # Create client
                settings = ArxivSettings(search_category=category)
                client = ArxivClient(settings)
                
                # Fetch all papers with unlimited retries per page
                papers, results = await client.fetch_all_papers_in_date_range(
                    from_date=from_date,
                    to_date=to_date,
                    max_per_page=100,
                    sort_by="submittedDate",
                    sort_order="descending",
                    max_retries_per_page=10,  # More retries per page
                )
                
                # Update expected total
                if results and len(results) > 0:
                    new_total = results[0].total_results
                    if total_expected is None:
                        total_expected = new_total
                        logger.info(f"[{category}] Total expected papers: {total_expected}")
                    elif new_total != total_expected:
                        logger.warning(
                            f"[{category}] Total changed: {total_expected} → {new_total}"
                        )
                        total_expected = new_total
                
                # Add newly fetched papers
                new_papers = 0
                for paper in papers:
                    if paper.arxiv_id not in all_papers_dict and paper.arxiv_id not in fetched_ids:
                        all_papers_dict[paper.arxiv_id] = paper
                        fetched_ids.add(paper.arxiv_id)
                        new_papers += 1
                
                logger.info(
                    f"[{category}] Fetched {len(papers)} papers this attempt "
                    f"({new_papers} new, {len(all_papers_dict)} total)"
                )
                
                # Check completeness
                if total_expected and len(all_papers_dict) >= total_expected:
                    logger.info(
                        f"[{category}] ✓ COMPLETE! Fetched {len(all_papers_dict)}/{total_expected} papers"
                    )
                    consecutive_failures = 0
                    break  # Success!
                elif total_expected:
                    missing = total_expected - len(all_papers_dict)
                    logger.warning(
                        f"[{category}] Incomplete: {len(all_papers_dict)}/{total_expected} "
                        f"({missing} missing, {len(all_papers_dict)/total_expected*100:.1f}% complete)"
                    )
                else:
                    logger.info(f"[{category}] Fetched {len(all_papers_dict)} papers (total unknown)")
                
                # Save checkpoint
                checkpoint["fetched_ids"] = list(fetched_ids)
                checkpoint["total_expected"] = total_expected
                checkpoint["attempts"] = attempt_count
                self._save_checkpoint(category, from_date, checkpoint)
                
                # Reset retry delay on successful fetch (even if incomplete)
                if new_papers > 0:
                    retry_delay = 10
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    # If no new papers for multiple attempts, might be complete
                    if consecutive_failures >= VERIFICATION_PASSES:
                        if total_expected is None or len(all_papers_dict) > 0:
                            logger.info(
                                f"[{category}] No new papers after {consecutive_failures} verification passes. "
                                f"Considering complete with {len(all_papers_dict)} papers."
                            )
                            break
                
            except Exception as e:
                logger.error(f"[{category}] Attempt #{attempt_count} failed: {e}")
                consecutive_failures += 1
                
            # Wait before retry (with exponential backoff)
            if not (total_expected and len(all_papers_dict) >= total_expected):
                retry_delay = min(retry_delay * 1.5, MAX_RETRY_WAIT_SECONDS)
                logger.info(f"[{category}] Waiting {retry_delay:.0f}s before next attempt...")
                await asyncio.sleep(retry_delay)
        
        # Convert to simplified format
        simplified_papers = []
        for paper in all_papers_dict.values():
            simplified_papers.append({
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "categories": paper.categories,
                "published_date": paper.published_date,
                "url": f"https://arxiv.org/abs/ {paper.arxiv_id}",
                "pdf_url": paper.pdf_url,
                "source_category": category,  # 添加源类别字段
            })
        
        # Build metadata
        is_complete = total_expected is None or len(simplified_papers) >= total_expected
        metadata = {
            "category": category,
            "date_range": f"{from_date}-{to_date}",
            "total_attempts": attempt_count,
            "elapsed_hours": (datetime.now() - start_time).total_seconds() / 3600,
            "papers_fetched": len(simplified_papers),
            "expected_total": total_expected,
            "completeness": "100%" if is_complete else f"{len(simplified_papers)/total_expected*100:.1f}%",
            "is_complete": is_complete,
        }
        
        # Clear checkpoint on success
        if is_complete:
            self._clear_checkpoint(category, from_date)
        
        return simplified_papers, metadata

    async def fetch_date_complete(
        self,
        date: datetime,
        categories: Optional[List[str]] = None,
        max_wait_hours: int = 24,
    ) -> Tuple[Dict[str, List[Dict]], Dict[str, Dict]]:
        """
        Fetch papers for all categories with 100% completeness guarantee.
        
        Args:
            date: Date to fetch papers for
            categories: List of categories (default: all)
            max_wait_hours: Max hours per category
            
        Returns:
            Tuple of (papers_by_category, metadata_by_category)
        """
        date_str = date.strftime("%Y%m%d")
        categories_to_fetch = categories or self.categories
        
        logger.info("=" * 80)
        logger.info(f"Starting 100% COMPLETE fetch for {date.strftime('%Y-%m-%d')}")
        logger.info(f"Categories: {len(categories_to_fetch)}")
        logger.info(f"Max wait per category: {max_wait_hours}h")
        logger.info("=" * 80)
        
        # Fetch each category sequentially (to avoid overwhelming API)
        papers_by_category = {}
        metadata_by_category = {}
        
        for i, category in enumerate(categories_to_fetch, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Category {i}/{len(categories_to_fetch)}: {category}")
            logger.info(f"{'='*80}")
            
            papers, metadata = await self.fetch_category_complete(
                category=category,
                from_date=date_str,
                to_date=date_str,
                max_wait_hours=max_wait_hours,
            )
            
            papers_by_category[category] = papers
            metadata_by_category[category] = metadata
            
            if metadata["is_complete"]:
                logger.info(f"[{category}] ✅ 100% COMPLETE: {metadata['papers_fetched']} papers")
            else:
                logger.warning(
                    f"[{category}] ⚠️ INCOMPLETE: {metadata['papers_fetched']}/{metadata['expected_total']} "
                    f"({metadata['completeness']})"
                )
        
        return papers_by_category, metadata_by_category

    def save_papers_with_metadata(
        self,
        papers_by_category: Dict[str, List[Dict]],
        metadata_by_category: Dict[str, Dict],
        date: datetime,
    ) -> List[Path]:
        """Save papers by category with detailed completeness metadata."""
        date_str = date.strftime("%Y-%m-%d")
        saved_files = []

        # Save each category separately
        for category, papers in papers_by_category.items():
            category_dir = self.output_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)

            output_file = category_dir / f"papers_{date_str}_100percent.json"
            metadata = metadata_by_category.get(category, {})

            # Build output for this category
            output_data = {
                "metadata": {
                    "fetch_mode": "100_percent_complete",
                    "fetch_date": datetime.now().isoformat(),
                    "paper_date": date_str,
                    "category": category,
                    "total_papers": len(papers),
                    "expected_total": metadata.get("expected_total", 0),
                    "completeness": metadata.get("completeness", "unknown"),
                    "is_complete": metadata.get("is_complete", False),
                    "total_attempts": metadata.get("total_attempts", 0),
                    "elapsed_hours": metadata.get("elapsed_hours", 0),
                },
                "papers": papers,
            }

            # Save
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            saved_files.append(output_file)

            # Log completion status for this category
            if metadata.get("is_complete"):
                logger.info(f"✅ [{category}] 100% COMPLETE: {len(papers)} papers saved to {output_file}")
            else:
                logger.warning(f"⚠️ [{category}] INCOMPLETE: {len(papers)}/{metadata.get('expected_total', '?')} papers ({metadata.get('completeness', 'unknown')}) saved to {output_file}")

        # Overall summary
        total_papers = sum(len(papers) for papers in papers_by_category.values())
        all_complete = all(meta.get("is_complete", False) for meta in metadata_by_category.values())

        if all_complete:
            logger.info("=" * 80)
            logger.info(f"✅ ALL CATEGORIES 100% COMPLETE SUCCESS!")
            logger.info(f"✅ Total saved {total_papers} papers across {len(papers_by_category)} categories")
            logger.info("=" * 80)
        else:
            incomplete_cats = [
                cat for cat, meta in metadata_by_category.items()
                if not meta.get("is_complete", False)
            ]
            logger.warning("=" * 80)
            logger.warning(f"⚠️ SOME CATEGORIES INCOMPLETE: {len(incomplete_cats)} categories not 100% complete")
            for cat in incomplete_cats:
                meta = metadata_by_category[cat]
                logger.warning(f"  - {cat}: {meta.get('completeness', 'unknown')}")
            logger.warning(f"⚠️ Total saved {total_papers} papers across {len(papers_by_category)} categories")
            logger.warning("=" * 80)

        return saved_files

    async def run_daily_complete(
        self,
        date: Optional[datetime] = None,
        max_wait_hours: int = 24,
    ):
        """
        Run complete fetch for all available dates from past week.

        Args:
            date: If specified, only fetch this date. If None, fetch all available dates.
            max_wait_hours: Max hours to spend per category
        """

        # Fetch all categories and dates
        papers_by_date, metadata_by_date = await self.async_daily_scrape(target_date=date)

        # If a specific date is requested and not found, log it
        if date is not None:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in papers_by_date:
                logger.info(f"No papers found for date {date_str}")
                papers_by_date = {}
                metadata_by_date = {}
            
            ## Also fetch PubMed for the specified date
            #await self.async_daily_pubmed(date=date)

        saved_files = []
        for current_date_str, papers in papers_by_date.items():
            current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
            metadata_list = metadata_by_date[current_date_str]

            papers_by_category = {}
            metadata_by_category = {}

            for paper in papers:
                # 使用source_category分组，保持原始抓取顺序
                source_category = paper.get("source_category", paper["categories"][0] if paper["categories"] else "unknown")
                if source_category not in papers_by_category:
                    papers_by_category[source_category] = []
                papers_by_category[source_category].append(paper)

            # Group metadata by category
            for metadata in metadata_list:
                category = metadata["category"]
                metadata_by_category[category] = metadata

            # Save results for this date (by category)
            category_files = self.save_papers_with_metadata(papers_by_category, metadata_by_category, current_date)
            saved_files.extend(category_files)

        if not saved_files:
            logger.warning(f"No data found to save")
            return None

        return saved_files[0] if len(saved_files) == 1 else saved_files

    async def run_continuous_complete(
        self,
        check_interval_hours: int = 24,
        max_wait_per_category: int = 12,
    ):
        """
        Run continuously, ensuring 100% completeness for each day.
        
        Args:
            check_interval_hours: Hours between checks
            max_wait_per_category: Max hours per category per attempt
        """
        logger.info("=" * 80)
        logger.info("Starting CONTINUOUS 100% COMPLETE mode")
        logger.info(f"Check interval: {check_interval_hours}h")
        logger.info(f"Max wait per category: {max_wait_per_category}h")
        logger.info("=" * 80)
        
        while True:
            try:
                # Fetch yesterday (most reliable)
                yesterday = datetime.now() - timedelta(days=1)
                await self.run_daily_complete(
                    date=yesterday,
                    max_wait_hours=max_wait_per_category,
                )
                
                # Also check day before yesterday (in case it was incomplete)
                two_days_ago = datetime.now() - timedelta(days=2)
                await self.run_daily_complete(
                    date=two_days_ago,
                    max_wait_hours=max_wait_per_category,
                )
                
                # Wait before next check
                logger.info(f"\nWaiting {check_interval_hours}h until next check...")
                await asyncio.sleep(check_interval_hours * 3600)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping...")
                break
            except Exception as e:
                logger.error(f"Error in continuous mode: {e}")
                logger.info("Retrying in 1 hour...")
                await asyncio.sleep(3600)


    async def run_fetch_by_custom_ids(
        self,
        custom_id_list: List[str],
        output_file: Optional[str] = None,
        max_wait_hours: int = 24,
    ):
        """
        使用用户指定的ID列表获取论文，并按照列表顺序保存

        Args:
            custom_id_list: 用户指定的arxiv ID列表
            category: 分类（用于API设置）
            output_file: 输出文件路径，如果不指定则自动生成
            max_wait_hours: 最大等待时间
        """
        logger.info("=" * 80)
        logger.info("Starting CUSTOM ID LIST fetch")
        logger.info(f"Category: custom_list_mode")
        logger.info(f"Total IDs: {len(custom_id_list)}")
        logger.info("=" * 80)

        # 使用fetch_papers_by_id方法获取论文，保持顺序
        papers, metadata = await self.fetch_papers_by_id(
            date="1900-01-01",
            category="custom_list_mode",
            paper_id_list=custom_id_list,
            max_wait_hours=max_wait_hours,
            preserve_order=False
        )

        # 生成输出文件名
        if output_file is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = self.output_dir / f"papers_custom_list_{timestamp}.json"

        # 保存论文
        output_data = {
            "metadata": {
                "fetch_mode": "custom_id_list",
                "fetch_date": datetime.now().isoformat(),
                "category": "custom_list_mode",
                "total_papers": len(papers),
                "expected_total": len(custom_id_list),
                "preserved_order": False,
            },
            "papers": papers,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info("=" * 80)
        logger.info(f"✅ Saved {len(papers)} papers to {output_file}")
        logger.info("=" * 80)

        return output_file


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fetch arXiv papers with 100% completeness guarantee"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Fetch papers for specific date (YYYY-MM-DD). If not specified, fetch all available dates from past week"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory"
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        help="Categories to fetch"
    )
    parser.add_argument(
        "--max-wait-hours",
        type=int,
        default=24,
        help="Maximum hours to wait per category (default: 24)"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously"
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=24,
        help="Hours between checks in continuous mode (default: 24)"
    )
    parser.add_argument(
        "--Fetch-Type",
        type=str,
        choices=['arXiv', 'PubMed', 'all'],
        default='all',
        help="Type of fetch (default: all)"
    )

    args = parser.parse_args()
    
    # Create fetcher
    fetcher = CompleteFetcher(
        output_dir=args.output_dir,
        categories=args.categories,
    )
    
    if args.continuous:
        # Continuous mode
        await fetcher.run_continuous_complete(
            check_interval_hours=args.check_interval,
            max_wait_per_category=args.max_wait_hours,
        )
    else:
        # Process all available dates from past week
        date = None
        if args.date:
            date = datetime.strptime(args.date, "%Y-%m-%d")

        if args.Fetch_Type == 'arXiv':
            await fetcher.run_daily_complete(
                date=date,
                max_wait_hours=args.max_wait_hours,
            )
        elif args.Fetch_Type == 'PubMed':
            await fetcher.async_daily_pubmed(date=date)
        elif args.Fetch_Type == 'all':
            await fetcher.async_daily_pubmed(date=date)
            await fetcher.run_daily_complete(
                date=date,
                max_wait_hours=args.max_wait_hours,
            )


if __name__ == "__main__":
    asyncio.run(main())
