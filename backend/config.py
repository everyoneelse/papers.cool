"""
Configuration settings for Cool Papers Backend
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Cool Papers API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./coolpapers.db"
    
    # Redis Cache (Optional)
    REDIS_URL: Optional[str] = None
    CACHE_ENABLED: bool = False
    CACHE_TTL: int = 3600  # 1 hour
    
    # ArXiv Settings
    ARXIV_BASE_URL: str = "https://arxiv.org"
    ARXIV_API_URL: str = "http://export.arxiv.org/api/query"
    ARXIV_RATE_LIMIT: float = 3.0  # seconds between requests
    
    # OpenReview Settings
    OPENREVIEW_API_URL: str = "https://api.openreview.net"
    
    # ACL Anthology
    ACL_BASE_URL: str = "https://aclanthology.org"
    
    # PMLR
    PMLR_BASE_URL: str = "https://proceedings.mlr.press"
    
    # Search Engine
    SEARCH_INDEX_PATH: str = "./search_index"
    SEARCH_MAX_RESULTS: int = 1000
    
    # PDF Processing
    PDF_CACHE_DIR: str = "./pdf_cache"
    PDF_MAX_SIZE_MB: int = 50
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # External API (Kimi - if you have access)
    KIMI_API_KEY: Optional[str] = None
    KIMI_API_URL: str = "https://api.moonshot.cn/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
