#!/usr/bin/env python3
"""
应用配置管理
统一的配置管理系统

运行环境: Python 3.11+
依赖: pydantic, pydantic-settings, typing
"""

import os
from functools import lru_cache
from typing import Dict, Any, List, Optional
from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    url: str = Field(default="sqlite:///./shrimp_agent.db", env="DATABASE_URL")
    echo: bool = Field(default=False, env="DATABASE_ECHO")
    pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    
    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis配置"""
    url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")
    max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    
    class Config:
        env_prefix = "REDIS_"


class LLMSettings(BaseSettings):
    """LLM配置"""
    providers: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "openai": {
            "enabled": False,
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "organization": ""
        },
        "anthropic": {
            "enabled": False,
            "api_key": "",
            "base_url": "https://api.anthropic.com"
        },
        "google": {
            "enabled": False,
            "api_key": "",
            "base_url": "https://generativelanguage.googleapis.com"
        },
        "local": {
            "enabled": False,
            "base_url": "http://localhost:8000",
            "model_path": ""
        }
    })
    load_balance_strategy: str = Field(default="round_robin")
    enable_fallback: bool = Field(default=True)
    max_retries: int = Field(default=3)
    timeout: float = Field(default=30.0)
    
    # 从环境变量读取API密钥
    @validator('providers', pre=True)
    def load_api_keys_from_env(cls, v):
        if isinstance(v, dict):
            # 从环境变量更新API密钥
            if "openai" in v and os.getenv("OPENAI_API_KEY"):
                v["openai"]["api_key"] = os.getenv("OPENAI_API_KEY")
                v["openai"]["enabled"] = True
            
            if "anthropic" in v and os.getenv("ANTHROPIC_API_KEY"):
                v["anthropic"]["api_key"] = os.getenv("ANTHROPIC_API_KEY")
                v["anthropic"]["enabled"] = True
            
            if "google" in v and os.getenv("GOOGLE_API_KEY"):
                v["google"]["api_key"] = os.getenv("GOOGLE_API_KEY")
                v["google"]["enabled"] = True
        
        return v
    
    class Config:
        env_prefix = "LLM_"


class RAGSettings(BaseSettings):
    """RAG配置"""
    document_processor: Dict[str, Any] = Field(default_factory=lambda: {
        "type": "enhanced",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "strategy": "fixed_size",
        "min_chunk_size": 100,
        "max_chunk_size": 2000,
        "dynamic_chunking": True
    })
    
    embedding: Dict[str, Any] = Field(default_factory=lambda: {
        "model": "text-embedding-ada-002",
        "api_key": "",
        "dimension": 1536,
        "batch_size": 100,
        "cache": {
            "enabled": True,
            "backend": "memory",
            "max_entries": 10000,
            "ttl_seconds": 7 * 24 * 3600
        }
    })
    
    vector_store: Dict[str, Any] = Field(default_factory=lambda: {
        "type": "faiss",
        "dimension": 1536,
        "index_path": "./data/faiss_index",
        "metadata_path": "./data/faiss_metadata.db"
    })
    
    retriever: Dict[str, Any] = Field(default_factory=lambda: {
        "default_top_k": 5,
        "default_threshold": 0.7,
        "enable_rerank": False,
        "query_expansion": False,
        "mmr_lambda": 0.5
    })
    
    engine: Dict[str, Any] = Field(default_factory=lambda: {
        "max_context_length": 4000,
        "answer_language": "zh-CN",
        "include_sources": True
    })
    
    # 从环境变量读取嵌入API密钥
    @validator('embedding', pre=True)
    def load_embedding_api_key(cls, v):
        if isinstance(v, dict) and os.getenv("OPENAI_API_KEY"):
            v["api_key"] = os.getenv("OPENAI_API_KEY")
        return v
    
    class Config:
        env_prefix = "RAG_"


class AgentSettings(BaseSettings):
    """智能体配置"""
    max_concurrent_agents: int = Field(default=10)
    default_timeout: float = Field(default=60.0)
    enable_camel_framework: bool = Field(default=True)
    
    available_agents: Dict[str, str] = Field(default_factory=lambda: {
        "coordinator": "coordinator_001",
        "searcher": "searcher_001",
        "extractor": "extractor_001",
        "analyzer": "analyzer_001"
    })
    
    workflows: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "simple_search": {
            "steps": [
                {"agent": "searcher", "task": "search"},
                {"agent": "analyzer", "task": "analyze"}
            ]
        },
        "deep_analysis": {
            "steps": [
                {"agent": "searcher", "task": "search"},
                {"agent": "extractor", "task": "extract"},
                {"agent": "analyzer", "task": "analyze"}
            ]
        }
    })
    
    class Config:
        env_prefix = "AGENT_"


class SearchSettings(BaseSettings):
    """搜索配置"""
    max_results: int = Field(default=20)
    default_timeout: float = Field(default=30.0)
    enable_web_search: bool = Field(default=True)
    enable_document_search: bool = Field(default=True)
    
    web_search_engines: List[str] = Field(default_factory=lambda: ["google", "bing"])
    
    search_strategies: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "similarity": {"weight": 1.0},
        "keyword": {"weight": 0.5},
        "hybrid": {"vector_weight": 0.7, "keyword_weight": 0.3}
    })
    
    class Config:
        env_prefix = "SEARCH_"


class DocumentSettings(BaseSettings):
    """文档配置"""
    upload_path: str = Field(default="./data/uploads")
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    allowed_extensions: List[str] = Field(default_factory=lambda: [
        ".txt", ".pdf", ".docx", ".html", ".md", ".json", ".csv"
    ])
    
    auto_process: bool = Field(default=True)
    backup_enabled: bool = Field(default=True)
    backup_path: str = Field(default="./data/backups")
    
    class Config:
        env_prefix = "DOCUMENT_"


class SecuritySettings(BaseSettings):
    """安全配置"""
    secret_key: str = Field(default="your-secret-key-change-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    
    # API密钥认证
    api_keys: List[str] = Field(default_factory=list)
    require_api_key: bool = Field(default=False)
    
    # 速率限制
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=60)  # 秒
    
    # CORS
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = Field(default=True)
    
    class Config:
        env_prefix = "SECURITY_"


class LoggingSettings(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_path: Optional[str] = Field(default=None)
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    backup_count: int = Field(default=5)
    
    # 结构化日志
    structured_logging: bool = Field(default=False)
    log_requests: bool = Field(default=True)
    log_responses: bool = Field(default=False)
    
    class Config:
        env_prefix = "LOGGING_"


class MonitoringSettings(BaseSettings):
    """监控配置"""
    enabled: bool = Field(default=True)
    metrics_endpoint: str = Field(default="/metrics")
    health_endpoint: str = Field(default="/health")
    
    # Prometheus配置
    prometheus_enabled: bool = Field(default=False)
    prometheus_port: int = Field(default=8001)
    
    # 性能监控
    track_performance: bool = Field(default=True)
    slow_query_threshold: float = Field(default=1.0)  # 秒
    
    class Config:
        env_prefix = "MONITORING_"


class Settings(BaseSettings):
    """主配置类"""
    # 应用基础配置
    app_name: str = Field(default="Shrimp Agent v2")
    version: str = Field(default="2.0.0")
    description: str = Field(default="现代化的智能搜索和RAG系统")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)
    
    # 环境
    environment: str = Field(default="development")
    
    # 数据目录
    data_dir: str = Field(default="./data")
    
    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    search: SearchSettings = Field(default_factory=SearchSettings)
    document: DocumentSettings = Field(default_factory=DocumentSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    @validator('debug', pre=True)
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v
    
    @validator('data_dir', pre=True)
    def create_data_dir(cls, v):
        data_path = Path(v)
        data_path.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        subdirs = ['uploads', 'backups', 'logs', 'faiss_index']
        for subdir in subdirs:
            (data_path / subdir).mkdir(exist_ok=True)
        
        return str(data_path)
    
    # 便捷属性
    @property
    def llm_config(self) -> Dict[str, Any]:
        """获取LLM配置字典"""
        return self.llm.dict()
    
    @property
    def rag_config(self) -> Dict[str, Any]:
        """获取RAG配置字典"""
        config = self.rag.dict()
        # 合并LLM配置
        config['llm_manager'] = None  # 将在运行时设置
        return config
    
    @property
    def agent_config(self) -> Dict[str, Any]:
        """获取智能体配置字典"""
        return self.agent.dict()
    
    @property
    def search_config(self) -> Dict[str, Any]:
        """获取搜索配置字典"""
        return self.search.dict()
    
    @property
    def document_config(self) -> Dict[str, Any]:
        """获取文档配置字典"""
        return self.document.dict()
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment.lower() == "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # 移除customise_sources方法，使用默认配置源


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


def get_database_url() -> str:
    """获取数据库URL"""
    settings = get_settings()
    return settings.database.url


def get_redis_url() -> str:
    """获取Redis URL"""
    settings = get_settings()
    return settings.redis.url


def is_debug_mode() -> bool:
    """是否为调试模式"""
    settings = get_settings()
    return settings.debug


def get_data_dir() -> Path:
    """获取数据目录路径"""
    settings = get_settings()
    return Path(settings.data_dir)


def get_upload_dir() -> Path:
    """获取上传目录路径"""
    settings = get_settings()
    return Path(settings.document.upload_path)


def get_backup_dir() -> Path:
    """获取备份目录路径"""
    settings = get_settings()
    return Path(settings.document.backup_path)


# 配置验证函数
def validate_settings() -> tuple[bool, List[str]]:
    """验证配置
    
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    try:
        settings = get_settings()
        
        # 验证必需的目录
        required_dirs = [
            settings.data_dir,
            settings.document.upload_path,
            settings.document.backup_path
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"无法创建目录 {dir_path}: {e}")
        
        # 验证LLM配置
        enabled_llm_providers = [
            name for name, config in settings.llm.providers.items()
            if config.get('enabled', False)
        ]
        
        if not enabled_llm_providers:
            errors.append("至少需要启用一个LLM提供商")
        
        # 验证API密钥
        for provider_name, provider_config in settings.llm.providers.items():
            if provider_config.get('enabled', False):
                if provider_name in ['openai', 'anthropic', 'google']:
                    if not provider_config.get('api_key'):
                        errors.append(f"{provider_name} 提供商缺少API密钥")
        
        # 验证端口
        if not (1 <= settings.port <= 65535):
            errors.append(f"无效的端口号: {settings.port}")
        
        # 验证文件大小限制
        if settings.document.max_file_size <= 0:
            errors.append("文件大小限制必须大于0")
        
    except Exception as e:
        errors.append(f"配置验证失败: {e}")
    
    return len(errors) == 0, errors


# 配置重载函数
def reload_settings():
    """重新加载配置"""
    get_settings.cache_clear()
    return get_settings()