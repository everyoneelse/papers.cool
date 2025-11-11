"""
PDF processing utilities for extracting text from papers
"""
import os
import hashlib
from pathlib import Path
from typing import Optional
import httpx
import fitz  # PyMuPDF
from loguru import logger

from config import settings


class PDFProcessor:
    """Process PDF files to extract text"""
    
    def __init__(self):
        self.cache_dir = Path(settings.PDF_CACHE_DIR)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_size_bytes = settings.PDF_MAX_SIZE_MB * 1024 * 1024
    
    def _get_cache_path(self, pdf_url: str) -> Path:
        """Get cache file path for a PDF URL"""
        url_hash = hashlib.md5(pdf_url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.txt"
    
    async def download_pdf(self, pdf_url: str) -> Optional[bytes]:
        """
        Download PDF from URL
        
        Args:
            pdf_url: URL to PDF file
            
        Returns:
            PDF content as bytes or None
        """
        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()
                
                # Check size
                content = response.content
                if len(content) > self.max_size_bytes:
                    logger.warning(f"PDF too large: {len(content)} bytes from {pdf_url}")
                    return None
                
                return content
                
        except Exception as e:
            logger.error(f"Error downloading PDF from {pdf_url}: {e}")
            return None
    
    def extract_text_from_bytes(self, pdf_bytes: bytes) -> Optional[str]:
        """
        Extract text from PDF bytes
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Extracted text or None
        """
        try:
            # Open PDF from bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                text_parts.append(text)
            
            doc.close()
            
            # Join all text
            full_text = "\n\n".join(text_parts)
            
            # Clean up text (remove excessive whitespace, etc.)
            full_text = self._clean_text(full_text)
            
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive newlines
        text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
        
        # Remove form feeds and other control characters
        text = text.replace("\f", "\n")
        text = text.replace("\r", "")
        
        # Normalize whitespace
        import re
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n\n+', '\n\n', text)
        
        return text.strip()
    
    async def extract_text(self, pdf_url: str, use_cache: bool = True) -> Optional[str]:
        """
        Extract text from PDF URL with caching
        
        Args:
            pdf_url: URL to PDF file
            use_cache: Whether to use cached results
            
        Returns:
            Extracted text or None
        """
        cache_path = self._get_cache_path(pdf_url)
        
        # Check cache first
        if use_cache and cache_path.exists():
            try:
                return cache_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.error(f"Error reading cache for {pdf_url}: {e}")
        
        # Download and extract
        pdf_bytes = await self.download_pdf(pdf_url)
        if not pdf_bytes:
            return None
        
        text = self.extract_text_from_bytes(pdf_bytes)
        
        # Save to cache
        if text and use_cache:
            try:
                cache_path.write_text(text, encoding='utf-8')
            except Exception as e:
                logger.error(f"Error saving cache for {pdf_url}: {e}")
        
        return text
    
    def extract_text_from_file(self, file_path: str) -> Optional[str]:
        """
        Extract text from local PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text or None
        """
        try:
            doc = fitz.open(file_path)
            
            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                text_parts.append(text)
            
            doc.close()
            
            full_text = "\n\n".join(text_parts)
            full_text = self._clean_text(full_text)
            
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return None
    
    def clear_cache(self):
        """Clear PDF text cache"""
        try:
            for file in self.cache_dir.glob("*.txt"):
                file.unlink()
            logger.info("PDF cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
