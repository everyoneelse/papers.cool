"""
Full-text search engine using Tantivy (BM25)
"""
import tantivy
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger

from config import settings


class SearchEngine:
    """Search engine for papers using Tantivy and BM25"""
    
    def __init__(self):
        self.index_path = Path(settings.SEARCH_INDEX_PATH)
        self.index_path.mkdir(exist_ok=True)
        
        # Define schema
        self.schema_builder = tantivy.SchemaBuilder()
        self.schema_builder.add_text_field("id", stored=True)
        self.schema_builder.add_text_field("title", stored=True)
        self.schema_builder.add_text_field("abstract", stored=True)
        self.schema_builder.add_text_field("authors", stored=True)
        self.schema_builder.add_text_field("full_text", stored=False)  # Don't store full text
        self.schema_builder.add_text_field("categories", stored=True)
        self.schema_builder.add_date_field("published_date", stored=True)
        self.schema_builder.add_text_field("venue", stored=True)
        self.schema = self.schema_builder.build()
        
        # Create or open index
        try:
            self.index = tantivy.Index(self.schema, path=str(self.index_path))
        except:
            # Index doesn't exist, create new
            self.index = tantivy.Index(self.schema)
            
        self.writer = None
        
    def _ensure_writer(self):
        """Ensure index writer is available"""
        if self.writer is None:
            self.writer = self.index.writer(heap_size=50_000_000)  # 50MB
    
    def add_paper(self, paper: Dict):
        """
        Add a paper to the search index
        
        Args:
            paper: Paper metadata dict
        """
        try:
            self._ensure_writer()
            
            # Prepare document
            doc = {
                "id": paper.get('id', ''),
                "title": paper.get('title', ''),
                "abstract": paper.get('abstract', ''),
                "authors": ' '.join(paper.get('authors', [])),
                "full_text": paper.get('full_text', ''),
                "categories": ' '.join(paper.get('categories', [])),
                "venue": paper.get('venue', ''),
            }
            
            # Add published date if available
            if paper.get('published_date'):
                doc["published_date"] = paper['published_date']
            
            self.writer.add_document(tantivy.Document(**doc))
            
        except Exception as e:
            logger.error(f"Error adding paper {paper.get('id')} to index: {e}")
    
    def add_papers_batch(self, papers: List[Dict]):
        """
        Add multiple papers to index in batch
        
        Args:
            papers: List of paper metadata dicts
        """
        self._ensure_writer()
        
        for paper in papers:
            self.add_paper(paper)
        
        # Commit batch
        try:
            self.writer.commit()
            self.writer = None  # Reset writer after commit
            logger.info(f"Added {len(papers)} papers to search index")
        except Exception as e:
            logger.error(f"Error committing papers to index: {e}")
    
    def search(self, query: str, max_results: int = None, 
               filter_venue: Optional[str] = None,
               filter_categories: Optional[List[str]] = None) -> List[Dict]:
        """
        Search papers by query
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            filter_venue: Filter by venue
            filter_categories: Filter by categories
            
        Returns:
            List of search results with paper metadata
        """
        if max_results is None:
            max_results = settings.SEARCH_MAX_RESULTS
        
        try:
            # Reload index to get latest changes
            self.index.reload()
            searcher = self.index.searcher()
            
            # Build query
            query_parser = tantivy.QueryParser.for_index(
                self.index,
                ["title", "abstract", "full_text", "authors"]
            )
            
            parsed_query = query_parser.parse_query(query)
            
            # Execute search with BM25 ranking
            search_results = searcher.search(parsed_query, limit=max_results)
            
            results = []
            for score, doc_address in search_results.hits:
                doc = searcher.doc(doc_address)
                
                # Convert to dict
                result = {
                    'id': doc.get_first('id'),
                    'title': doc.get_first('title'),
                    'abstract': doc.get_first('abstract'),
                    'authors': doc.get_first('authors', '').split() if doc.get_first('authors') else [],
                    'categories': doc.get_first('categories', '').split() if doc.get_first('categories') else [],
                    'venue': doc.get_first('venue'),
                    'score': score
                }
                
                # Apply filters
                if filter_venue and result['venue'] != filter_venue:
                    continue
                    
                if filter_categories:
                    if not any(cat in result['categories'] for cat in filter_categories):
                        continue
                
                results.append(result)
            
            logger.info(f"Search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")
            return []
    
    def search_by_title(self, title: str, max_results: int = 10) -> List[Dict]:
        """Search papers by title only"""
        try:
            self.index.reload()
            searcher = self.index.searcher()
            
            query_parser = tantivy.QueryParser.for_index(self.index, ["title"])
            parsed_query = query_parser.parse_query(title)
            
            search_results = searcher.search(parsed_query, limit=max_results)
            
            results = []
            for score, doc_address in search_results.hits:
                doc = searcher.doc(doc_address)
                results.append({
                    'id': doc.get_first('id'),
                    'title': doc.get_first('title'),
                    'score': score
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching by title '{title}': {e}")
            return []
    
    def delete_paper(self, paper_id: str):
        """
        Delete a paper from index
        
        Args:
            paper_id: Paper ID to delete
        """
        try:
            self._ensure_writer()
            
            # Delete by term (id field)
            self.writer.delete_documents("id", paper_id)
            self.writer.commit()
            self.writer = None
            
            logger.info(f"Deleted paper {paper_id} from index")
            
        except Exception as e:
            logger.error(f"Error deleting paper {paper_id} from index: {e}")
    
    def optimize_index(self):
        """Optimize the search index (merge segments)"""
        try:
            self._ensure_writer()
            self.writer.commit()
            self.writer = None
            
            # Note: Tantivy doesn't have explicit optimize in Python binding
            # But committing helps consolidate the index
            logger.info("Index optimized")
            
        except Exception as e:
            logger.error(f"Error optimizing index: {e}")
    
    def clear_index(self):
        """Clear all documents from index"""
        try:
            # Delete and recreate index
            import shutil
            if self.index_path.exists():
                shutil.rmtree(self.index_path)
            self.index_path.mkdir(exist_ok=True)
            
            self.index = tantivy.Index(self.schema)
            self.writer = None
            
            logger.info("Search index cleared")
            
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
