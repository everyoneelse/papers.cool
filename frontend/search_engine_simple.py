"""
简化的 BM25 搜索引擎 - 兼容所有 tantivy 版本
使用最简单的 API，避免版本兼容性问题
"""
import tantivy
from pathlib import Path
from typing import List, Dict, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimplePaperSearchEngine:
    """
    简化的论文搜索引擎
    
    使用 tantivy 的最简单 API，兼容性最好
    """
    
    def __init__(self, index_path: str = "./search_index"):
        """初始化搜索引擎"""
        self.index_path = Path(index_path)
        self.index_path.mkdir(exist_ok=True, parents=True)
        
        # 定义 schema
        schema_builder = tantivy.SchemaBuilder()
        schema_builder.add_text_field("id", stored=True)
        schema_builder.add_text_field("title", stored=True)
        schema_builder.add_text_field("abstract", stored=True)
        schema_builder.add_text_field("authors", stored=True)
        schema_builder.add_text_field("categories", stored=True)
        schema_builder.add_text_field("published_date", stored=True)
        
        # 添加一个组合字段用于搜索
        schema_builder.add_text_field("search_text", stored=False)
        
        self.schema = schema_builder.build()
        
        # 创建或打开索引
        try:
            self.index = tantivy.Index(self.schema, path=str(self.index_path))
            logger.info(f"Opened existing index at {self.index_path}")
        except:
            self.index = tantivy.Index(self.schema)
            logger.info(f"Created new index")
    
    def build_index(self, papers: List[Dict]):
        """从论文列表构建索引"""
        logger.info(f"Building index from {len(papers)} papers...")
        
        try:
            writer = self.index.writer(heap_size=50_000_000)
            
            for paper in papers:
                try:
                    paper_id = str(paper.get('arxiv_id') or paper.get('id', ''))
                    title = paper.get('title', '')
                    abstract = paper.get('abstract', '')
                    authors_list = paper.get('authors', [])
                    authors = ' '.join(authors_list) if isinstance(authors_list, list) else str(authors_list)
                    categories_list = paper.get('categories', [])
                    categories = ' '.join(categories_list) if isinstance(categories_list, list) else str(categories_list)
                    published_date = str(paper.get('published_date', ''))
                    
                    # 创建组合搜索文本
                    search_text = f"{title} {abstract} {authors}"
                    
                    # 创建文档
                    doc = tantivy.Document()
                    doc.add_text("id", paper_id)
                    doc.add_text("title", title)
                    doc.add_text("abstract", abstract)
                    doc.add_text("authors", authors)
                    doc.add_text("categories", categories)
                    doc.add_text("published_date", published_date)
                    doc.add_text("search_text", search_text)
                    
                    writer.add_document(doc)
                    
                except Exception as e:
                    logger.warning(f"Error adding paper {paper.get('id')}: {e}")
                    continue
            
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
        """搜索论文"""
        if not query or not query.strip():
            return []
        
        try:
            self.index.reload()
            searcher = self.index.searcher()
            
            # 使用最简单的查询方式
            # 在 search_text 字段中搜索
            query_obj = self.index.parse_query(query, ["search_text"])
            
            # 执行搜索
            search_results = searcher.search(query_obj, limit=max_results)
            
            # 处理结果
            results = []
            for score, doc_address in search_results.hits:
                doc = searcher.doc(doc_address)
                
                result = {
                    'id': doc.get_first('id'),
                    'title': doc.get_first('title'),
                    'abstract': doc.get_first('abstract'),
                    'authors': doc.get_first('authors', '').split() if doc.get_first('authors') else [],
                    'categories': doc.get_first('categories', '').split() if doc.get_first('categories') else [],
                    'published_date': doc.get_first('published_date'),
                    'search_score': float(score),
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
    
    def get_index_stats(self) -> Dict:
        """获取索引统计"""
        try:
            self.index.reload()
            searcher = self.index.searcher()
            num_docs = searcher.num_docs()
            
            return {
                'num_documents': num_docs,
                'index_path': str(self.index_path),
                'status': 'ready' if num_docs > 0 else 'empty'
            }
        except Exception as e:
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
            
            self.index_path.mkdir(exist_ok=True, parents=True)
            self.index = tantivy.Index(self.schema)
            logger.info("Index cleared")
            
        except Exception as e:
            logger.error(f"Error clearing index: {e}")


def simple_search_papers(
    query: str, 
    papers: List[Dict],
    categories: Optional[List[str]] = None,
    search_engine: Optional[SimplePaperSearchEngine] = None
) -> List[Dict]:
    """
    便捷搜索函数
    
    Args:
        query: 搜索关键词
        papers: 论文列表
        categories: 分类过滤
        search_engine: 搜索引擎实例（可选）
        
    Returns:
        搜索结果列表
    """
    if not query or not query.strip():
        return papers
    
    # 创建或使用搜索引擎
    if search_engine is None:
        search_engine = SimplePaperSearchEngine()
    
    # 检查是否需要构建索引
    stats = search_engine.get_index_stats()
    if stats['num_documents'] == 0:
        logger.info("Building search index...")
        search_engine.build_index(papers)
    
    # 执行搜索
    search_results = search_engine.search(
        query, 
        max_results=1000,
        filter_categories=categories
    )
    
    # 合并结果
    paper_dict = {}
    for paper in papers:
        paper_id = paper.get('arxiv_id') or paper.get('id')
        if paper_id:
            paper_dict[str(paper_id)] = paper
    
    merged_results = []
    for result in search_results:
        paper_id = result.get('id')
        if paper_id in paper_dict:
            paper = paper_dict[paper_id].copy()
            paper['search_score'] = result.get('search_score', 0)
            merged_results.append(paper)
        else:
            merged_results.append(result)
    
    return merged_results
