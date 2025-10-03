#!/usr/bin/env python3
"""
RAG引擎基础接口定义
提供检索增强生成的核心抽象

运行环境: Python 3.11+
依赖: typing, abc, dataclasses
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from enum import Enum
from datetime import datetime


class DocumentType(Enum):
    """文档类型"""
    TEXT = "text"
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"
    DOCX = "docx"
    XLSX = "xlsx"


class ChunkingStrategy(Enum):
    """分块策略"""
    FIXED_SIZE = "fixed_size"  # 固定大小
    SEMANTIC = "semantic"  # 语义分块
    SENTENCE = "sentence"  # 句子分块
    PARAGRAPH = "paragraph"  # 段落分块
    RECURSIVE = "recursive"  # 递归分块


class EmbeddingModel(Enum):
    """嵌入模型"""
    OPENAI_ADA = "text-embedding-ada-002"
    OPENAI_3_SMALL = "text-embedding-3-small"
    OPENAI_3_LARGE = "text-embedding-3-large"
    SENTENCE_TRANSFORMERS = "sentence-transformers"
    BGE_LARGE = "bge-large-zh"
    BGE_BASE = "bge-base-zh"


class VectorStoreType(Enum):
    """向量存储类型"""
    FAISS = "faiss"
    CHROMA = "chroma"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"
    MILVUS = "milvus"
    ELASTICSEARCH = "elasticsearch"


class RetrievalStrategy(Enum):
    """检索策略"""
    SIMILARITY = "similarity"  # 相似度检索
    MMR = "mmr"  # 最大边际相关性
    HYBRID = "hybrid"  # 混合检索
    KEYWORD = "keyword"  # 关键词检索
    SEMANTIC_HYBRID = "semantic_hybrid"  # 语义混合


@dataclass
class Document:
    """文档数据结构"""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    doc_id: Optional[str] = None
    doc_type: DocumentType = DocumentType.TEXT
    source: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    language: str = "zh-CN"
    
    def __post_init__(self):
        if self.doc_id is None:
            import uuid
            self.doc_id = str(uuid.uuid4())
        
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class DocumentChunk:
    """文档块数据结构"""
    content: str
    chunk_id: str
    doc_id: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    chunk_type: str = "text"
    overlap_with_prev: int = 0
    overlap_with_next: int = 0
    
    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = f"{self.doc_id}_chunk_{self.chunk_index}"


@dataclass
class RetrievalQuery:
    """检索查询"""
    query: str
    top_k: int = 5
    strategy: RetrievalStrategy = RetrievalStrategy.SIMILARITY
    filters: Dict[str, Any] = field(default_factory=dict)
    threshold: float = 0.7
    include_metadata: bool = True
    rerank: bool = False
    expand_query: bool = False
    query_embedding: Optional[List[float]] = None


@dataclass
class RetrievalResult:
    """检索结果"""
    chunk: DocumentChunk
    score: float
    rank: int
    retrieval_method: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGResponse:
    """RAG响应"""
    query: str
    answer: str
    retrieved_chunks: List[RetrievalResult]
    sources: List[str]
    confidence: float
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    model_used: Optional[str] = None
    total_tokens: Optional[int] = None


class RAGError(Exception):
    """RAG基础异常"""
    pass


class DocumentProcessingError(RAGError):
    """文档处理异常"""
    pass


class EmbeddingError(RAGError):
    """嵌入生成异常"""
    pass


class RetrievalError(RAGError):
    """检索异常"""
    pass


class VectorStoreError(RAGError):
    """向量存储异常"""
    pass


class BaseDocumentProcessor(ABC):
    """文档处理器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def process_document(self, document: Document) -> List[DocumentChunk]:
        """处理文档，生成文档块
        
        Args:
            document: 输入文档
            
        Returns:
            文档块列表
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            配置是否有效
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[DocumentType]:
        """获取支持的文档类型
        
        Returns:
            支持的文档类型列表
        """
        pass


class BaseEmbeddingProvider(ABC):
    """嵌入提供商基类"""
    
    def __init__(self, model: EmbeddingModel, config: Dict[str, Any]):
        self.model = model
        self.config = config
        self.dimension = config.get('dimension', 1536)
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """生成文本嵌入
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量
        """
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            配置是否有效
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            服务是否健康
        """
        pass


class BaseVectorStore(ABC):
    """向量存储基类"""
    
    def __init__(self, store_type: VectorStoreType, config: Dict[str, Any]):
        self.store_type = store_type
        self.config = config
        self.dimension = config.get('dimension', 1536)
    
    @abstractmethod
    async def add_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """添加文档块
        
        Args:
            chunks: 文档块列表
            
        Returns:
            是否添加成功
        """
        pass
    
    @abstractmethod
    async def search(self, query_embedding: List[float], 
                    top_k: int = 5, 
                    filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """向量搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            检索结果列表
        """
        pass
    
    @abstractmethod
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """删除文档块
        
        Args:
            chunk_ids: 文档块ID列表
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def update_chunk(self, chunk: DocumentChunk) -> bool:
        """更新文档块
        
        Args:
            chunk: 文档块
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        """获取文档块
        
        Args:
            chunk_id: 文档块ID
            
        Returns:
            文档块或None
        """
        pass
    
    @abstractmethod
    async def list_chunks(self, doc_id: Optional[str] = None, 
                         limit: int = 100, 
                         offset: int = 0) -> List[DocumentChunk]:
        """列出文档块
        
        Args:
            doc_id: 文档ID过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            文档块列表
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            配置是否有效
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            存储是否健康
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息
        """
        pass


class BaseRetriever(ABC):
    """检索器基类"""
    
    def __init__(self, vector_store: BaseVectorStore, 
                 embedding_provider: BaseEmbeddingProvider,
                 config: Dict[str, Any]):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.config = config
    
    @abstractmethod
    async def retrieve(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """执行检索
        
        Args:
            query: 检索查询
            
        Returns:
            检索结果列表
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            配置是否有效
        """
        pass


class BaseRAGEngine(ABC):
    """RAG引擎基类"""
    
    def __init__(self, 
                 document_processor: BaseDocumentProcessor,
                 embedding_provider: BaseEmbeddingProvider,
                 vector_store: BaseVectorStore,
                 retriever: BaseRetriever,
                 config: Dict[str, Any]):
        self.document_processor = document_processor
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.retriever = retriever
        self.config = config
    
    @abstractmethod
    async def add_document(self, document: Document) -> bool:
        """添加文档
        
        Args:
            document: 文档
            
        Returns:
            是否添加成功
        """
        pass
    
    @abstractmethod
    async def query(self, query: str, **kwargs) -> RAGResponse:
        """执行RAG查询
        
        Args:
            query: 查询文本
            **kwargs: 其他参数
            
        Returns:
            RAG响应
        """
        pass
    
    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def update_document(self, document: Document) -> bool:
        """更新文档
        
        Args:
            document: 文档
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            配置是否有效
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, bool]:
        """健康检查
        
        Returns:
            各组件健康状态
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息
        """
        pass