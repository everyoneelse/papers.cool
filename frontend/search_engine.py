"""
简化的 BM25 搜索引擎 - 可直接在 Streamlit 中使用
基于 Tantivy，无需依赖 Backend 的其他模块
"""
import tantivy
from pathlib import Path
from typing import List, Dict, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperSearchEngine:
    """
    论文搜索引擎 - 使用 Tantivy + BM25
    
    可以直接在 Streamlit 中使用，无需启动 Backend API
    """
    
    def __init__(self, index_path: str = "./search_index"):
        """
        初始化搜索引擎
        
        Args:
            index_path: 索引存储路径
        """
        self.index_path = Path(index_path)
        self.index_path.mkdir(exist_ok=True, parents=True)
        
        # 定义 schema
        self.schema_builder = tantivy.SchemaBuilder()
        self.schema_builder.add_text_field("id", stored=True)
        self.schema_builder.add_text_field("title", stored=True)
        self.schema_builder.add_text_field("abstract", stored=True)
        self.schema_builder.add_text_field("authors", stored=True)
        self.schema_builder.add_text_field("categories", stored=True)
        self.schema_builder.add_text_field("published_date", stored=True)
        self.schema = self.schema_builder.build()
        
        # 创建或打开索引
        try:
            self.index = tantivy.Index(self.schema, path=str(self.index_path))
            logger.info(f"Opened existing index at {self.index_path}")
        except:
            # 索引不存在，创建新的
            self.index = tantivy.Index(self.schema)
            logger.info(f"Created new index at {self.index_path}")
        
        self.writer = None
    
    def build_index_from_papers(self, papers: List[Dict]):
        """
        从论文列表构建搜索索引
        
        Args:
            papers: 论文列表，每个论文是一个字典
        """
        logger.info(f"Building search index from {len(papers)} papers...")
        
        try:
            # 创建 writer
            writer = self.index.writer(heap_size=50_000_000)  # 50MB
            
            # 添加每篇论文到索引
            for paper in papers:
                try:
                    # 准备文档数据
                    doc_data = {
                        "id": str(paper.get('arxiv_id') or paper.get('id', '')),
                        "title": paper.get('title', ''),
                        "abstract": paper.get('abstract', ''),
                        "authors": ' '.join(paper.get('authors', [])),
                        "categories": ' '.join(paper.get('categories', [])),
                        "published_date": str(paper.get('published_date', '')),
                    }
                    
                    # 创建 tantivy 文档
                    doc = tantivy.Document()
                    for field, value in doc_data.items():
                        if value:  # 只添加非空值
                            doc.add_text(field, value)
                    
                    writer.add_document(doc)
                    
                except Exception as e:
                    logger.warning(f"Error adding paper {paper.get('id')}: {e}")
                    continue
            
            # 提交索引
            writer.commit()
            logger.info(f"Successfully built index with {len(papers)} papers")
            
        except Exception as e:
            logger.error(f"Error building index: {e}")
            raise
    
    def search(
        self, 
        query: str, 
        max_results: int = 100,
        filter_categories: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        搜索论文（使用 BM25 排序）
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            filter_categories: 过滤的分类列表
            
        Returns:
            搜索结果列表，按相关性（BM25 分数）排序
        """
        if not query or not query.strip():
            return []
        
        try:
            # 重新加载索引（获取最新数据）
            self.index.reload()
            searcher = self.index.searcher()
            
            # 构建查询 - 兼容不同版本的 tantivy API
            try:
                # 尝试新版本 API (0.21+)
                if hasattr(tantivy, 'QueryParser'):
                    query_parser = tantivy.QueryParser.for_index(
                        self.index,
                        ["title", "abstract", "authors"]
                    )
                    parsed_query = query_parser.parse_query(query)
                else:
                    # 使用索引对象的方法
                    parsed_query = self.index.parse_query(
                        query,
                        ["title", "abstract", "authors"]
                    )
            except AttributeError:
                # 备用方案：使用更简单的 API
                # 获取 schema 中的字段
                title_field = self.schema.get_field("title")
                abstract_field = self.schema.get_field("abstract")
                authors_field = self.schema.get_field("authors")
                
                # 创建多字段查询
                query_lower = query.lower()
                parsed_query = self.index.parse_query(query_lower)
            
            # 执行搜索（BM25 排序）
            search_results = searcher.search(parsed_query, limit=max_results)
            
            # 处理结果
            results = []
            for score, doc_address in search_results.hits:
                doc = searcher.doc(doc_address)
                
                # 提取文档字段
                result = {
                    'id': doc.get_first('id'),
                    'title': doc.get_first('title'),
                    'abstract': doc.get_first('abstract'),
                    'authors': doc.get_first('authors', '').split() if doc.get_first('authors') else [],
                    'categories': doc.get_first('categories', '').split() if doc.get_first('categories') else [],
                    'published_date': doc.get_first('published_date'),
                    'search_score': float(score),  # BM25 相关性分数
                }
                
                # 应用分类过滤
                if filter_categories:
                    if not any(cat in result['categories'] for cat in filter_categories):
                        continue
                
                results.append(result)
            
            logger.info(f"Search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def search_by_title_only(self, title: str, max_results: int = 10) -> List[Dict]:
        """
        只在标题中搜索
        
        Args:
            title: 标题关键词
            max_results: 最大结果数
            
        Returns:
            搜索结果列表
        """
        try:
            self.index.reload()
            searcher = self.index.searcher()
            
            # 兼容不同版本的 API
            try:
                if hasattr(tantivy, 'QueryParser'):
                    query_parser = tantivy.QueryParser.for_index(self.index, ["title"])
                    parsed_query = query_parser.parse_query(title)
                else:
                    parsed_query = self.index.parse_query(title, ["title"])
            except AttributeError:
                parsed_query = self.index.parse_query(title)
            
            search_results = searcher.search(parsed_query, limit=max_results)
            
            results = []
            for score, doc_address in search_results.hits:
                doc = searcher.doc(doc_address)
                results.append({
                    'id': doc.get_first('id'),
                    'title': doc.get_first('title'),
                    'search_score': float(score)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching by title '{title}': {e}")
            return []
    
    def get_index_stats(self) -> Dict:
        """
        获取索引统计信息
        
        Returns:
            包含索引统计的字典
        """
        try:
            self.index.reload()
            searcher = self.index.searcher()
            
            # 获取文档总数
            num_docs = searcher.num_docs()
            
            return {
                'num_documents': num_docs,
                'index_path': str(self.index_path),
                'status': 'ready' if num_docs > 0 else 'empty'
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {
                'num_documents': 0,
                'index_path': str(self.index_path),
                'status': 'error',
                'error': str(e)
            }
    
    def clear_index(self):
        """清空索引"""
        try:
            import shutil
            if self.index_path.exists():
                shutil.rmtree(self.index_path)
                logger.info("Index cleared")
            
            self.index_path.mkdir(exist_ok=True, parents=True)
            self.index = tantivy.Index(self.schema)
            self.writer = None
            
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            raise


# ===== 兼容性包装函数（可选） =====

def search_papers_bm25(
    query: str, 
    papers: List[Dict],
    categories: Optional[List[str]] = None,
    search_engine: Optional[PaperSearchEngine] = None,
    rebuild_index: bool = False
) -> List[Dict]:
    """
    使用 BM25 搜索论文的便捷函数
    
    Args:
        query: 搜索关键词
        papers: 论文列表（用于构建索引）
        categories: 分类过滤
        search_engine: 已存在的搜索引擎实例（可选）
        rebuild_index: 是否重新构建索引
        
    Returns:
        搜索结果列表（包含完整论文信息）
    """
    if not query or not query.strip():
        return papers
    
    # 创建或使用搜索引擎
    if search_engine is None:
        search_engine = PaperSearchEngine()
    
    # 检查索引是否需要构建
    stats = search_engine.get_index_stats()
    if stats['num_documents'] == 0 or rebuild_index:
        logger.info("Building search index...")
        search_engine.build_index_from_papers(papers)
    
    # 执行搜索
    search_results = search_engine.search(
        query, 
        max_results=1000,
        filter_categories=categories
    )
    
    # 将搜索结果与完整论文信息合并
    paper_dict = {}
    for paper in papers:
        paper_id = paper.get('arxiv_id') or paper.get('id')
        if paper_id:
            paper_dict[str(paper_id)] = paper
    
    # 合并结果
    merged_results = []
    for result in search_results:
        paper_id = result.get('id')
        if paper_id in paper_dict:
            # 使用完整的论文数据
            paper = paper_dict[paper_id].copy()
            paper['search_score'] = result.get('search_score', 0)
            merged_results.append(paper)
        else:
            # 使用搜索结果中的数据
            merged_results.append(result)
    
    return merged_results
