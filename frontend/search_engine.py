"""
简化的 BM25 搜索引擎 - 可直接在 Streamlit 中使用
基于 Tantivy，无需依赖 Backend 的其他模块
"""
import tantivy
from pathlib import Path
from typing import List, Dict, Optional
import logging

# 创建英文 stemmer analyzer with stopwords
tokenizer = tantivy.Tokenizer.whitespace()
stemmer_filter = tantivy.Filter.stemmer('english')

# 获取 NLTK 停用词（带缓存和自动下载）
def get_stopwords():
    try:
        import nltk
        try:
            return set(nltk.corpus.stopwords.words('english'))
        except LookupError:
            nltk.download('stopwords', quiet=True)
            return set(nltk.corpus.stopwords.words('english'))
    except ImportError:
        # 后备方案：如果未安装 nltk，使用内置的最小列表
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'i', 'me', 'my', 'myself', 'we', 'our',
            'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
            'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his'
        }

STOPWORDS = get_stopwords()

# 添加停用词过滤（常见的英文停用词）
# 注意：Tantivy 可能没有内置的停用词列表，这里展示概念
# 实际使用时可能需要在查询预处理阶段手动移除停用词
stemmer_analyzer = tantivy.TextAnalyzerBuilder(tokenizer).filter(stemmer_filter).build()

# 配置日志

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
        self.schema_builder.add_text_field("title", stored=True, tokenizer_name="en_stem")
        self.schema_builder.add_text_field("abstract", stored=True, tokenizer_name="en_stem")
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

        # 注册 stemmer tokenizer
        self.index.register_tokenizer("en_stem", stemmer_analyzer)

        self.writer = None
    
    def build_index_from_papers(self, papers: List[Dict], keywords_dicts: Dict[str, List[str]] = {}):
        """
        从论文列表构建搜索索引
        
        Args:
            papers: 论文列表，每个论文是一个字典
            keywords_lists: 关键词列表，每个关键词列表是一个列表
        """
        logger.info(f"Building search index from {len(papers)} papers...")
        
        try:
            # 创建 writer
            writer = self.index.writer(heap_size=50_000_000)  # 50MB
            
            # 添加每篇论文到索引
            for idx, paper in enumerate(papers):
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
    
    def _has_advanced_syntax(self, query: str) -> bool:
        """检查查询是否包含高级语法（AND, OR, 括号, 引号）"""
        query_upper = query.upper()
        return (
            ' AND ' in query_upper or 
            ' OR ' in query_upper or 
            ' NOT ' in query_upper or
            '(' in query or 
            ')' in query or
            '"' in query or
            '+' in query or
            '-' in query
        )
    
    def _preprocess_query_with_stopwords(self, query: str) -> str:
        """预处理查询，移除停用词但保留高级语法"""
        if not self._has_advanced_syntax(query):
            words = [w for w in query.lower().split() if w not in STOPWORDS]
            return ' '.join(words) if words else ''
        
        import re
        tokens = re.split(r'(\s+AND\s+|\s+OR\s+|\s+NOT\s+|[()"])', query, flags=re.IGNORECASE)
        result = []
        for token in tokens:
            token_upper = token.upper().strip()
            if token_upper in ['AND', 'OR', 'NOT', '(', ')', '"', '']:
                result.append(token)
            elif token.startswith('"') or token.endswith('"'):
                result.append(token)
            else:
                words = [w for w in token.lower().split() if w not in STOPWORDS]
                result.append(' '.join(words))
        return ''.join(result)

    def search(
        self, 
        query: str, 
        max_results: int = 100,
        filter_categories: Optional[List[str]] = None,
        phrase_search: bool = False,
        require_all_words: bool = False,
        remove_stopwords: bool = False,
    ) -> List[Dict]:
        """
        搜索论文（使用 BM25 排序）
        
        Args:
            query: 搜索关键词，支持高级语法：
                - AND: "transformer AND attention" 两个词都必须出现
                - OR: "GPT OR LLM" 任意一个出现即可
                - NOT: "transformer NOT BERT" 包含transformer但不包含BERT
                - 括号: "(large language model) AND vision"
                - 短语: '"large language model"' 严格短语匹配
                - +/-: "+transformer -BERT" 必须包含/排除
            max_results: 最大返回结果数
            filter_categories: 过滤的分类列表
            phrase_search: 是否使用短语搜索（默认False，仅在无高级语法时生效）
            require_all_words: 是否要求所有词都出现（默认False，仅在无高级语法时生效）
            remove_stopwords: 是否移除停用词（默认False）
        Returns:
            搜索结果列表，按相关性（BM25 分数）排序
        """
        if not query or not query.strip():
            return []
        
        try:
            self.index.reload()
            searcher = self.index.searcher()
            
            search_query = query.strip()
            
            has_advanced = self._has_advanced_syntax(search_query)
            
            if remove_stopwords:
                if has_advanced:
                    search_query = self._preprocess_query_with_stopwords(search_query)
                else:
                    words = [w for w in search_query.lower().split() if w not in STOPWORDS]
                    if words:
                        search_query = ' '.join(words)
                    else:
                        logger.warning(f"Query contains only stopwords: '{query}'")
                        return []
            
            if not has_advanced:
                if phrase_search and ' ' in search_query and not search_query.startswith('"'):
                    search_query = f'"{search_query}"'
                elif require_all_words and ' ' in search_query:
                    words = search_query.split()
                    search_query = ' AND '.join(words)
            
            parsed_query = self.index.parse_query(
                search_query,
                default_field_names=["title", "abstract", "authors"]
            )
            
            # 执行搜索（BM25 排序）
            search_results = searcher.search(parsed_query, limit=max_results)
            
            # 处理结果
            results = []
            for score, doc_address in search_results.hits:
                doc = searcher.doc(doc_address)

                # 使用 to_dict() 获取所有字段值
                doc_dict = doc.to_dict()

                # 提取文档字段（tantivy返回的都是列表，需要取第一个元素）
                result = {
                    'id': doc_dict.get('id', [None])[0],
                    'title': doc_dict.get('title', [None])[0],
                    'abstract': doc_dict.get('abstract', [None])[0],
                    'authors': doc_dict.get('authors', [''])[0].split() if doc_dict.get('authors') and doc_dict['authors'][0] else [],
                    'categories': doc_dict.get('categories', [''])[0].split() if doc_dict.get('categories') and doc_dict['categories'][0] else [],
                    'published_date': doc_dict.get('published_date', [None])[0],
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
            
            parsed_query = self.index.parse_query(
                title,
                default_field_names=["title"]
            )
            
            search_results = searcher.search(parsed_query, limit=max_results)
            
            results = []
            for score, doc_address in search_results.hits:
                doc = searcher.doc(doc_address)
                doc_dict = doc.to_dict()
                results.append({
                    'id': doc_dict.get('id', [None])[0],
                    'title': doc_dict.get('title', [None])[0],
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
            num_docs = searcher.num_docs
            
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
        if rebuild_index:
            # 如果强制重建，先清空索引
            search_engine.clear_index()
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
