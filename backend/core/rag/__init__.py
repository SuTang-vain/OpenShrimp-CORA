#!/usr/bin/env python3
"""
RAG引擎模块初始化文件
导出检索增强生成的核心接口和实现

运行环境: Python 3.11+
依赖: typing, asyncio
"""

# 基础接口和数据类
from .base import (
    # 枚举类型
    DocumentType,
    ChunkingStrategy,
    EmbeddingModel,
    VectorStoreType,
    RetrievalStrategy,
    
    # 数据类
    Document,
    DocumentChunk,
    RetrievalQuery,
    RetrievalResult,
    RAGResponse,
    
    # 异常类
    RAGError,
    DocumentProcessingError,
    EmbeddingError,
    RetrievalError,
    VectorStoreError,
    
    # 基础接口
    BaseDocumentProcessor,
    BaseEmbeddingProvider,
    BaseVectorStore,
    BaseRetriever,
    BaseRAGEngine
)

# 文档处理器
from .processors import (
    TextDocumentProcessor,
    JSONDocumentProcessor,
    HTMLDocumentProcessor,
    EnhancedDocumentProcessor
)

# 嵌入提供商
from .embeddings import (
    OpenAIEmbeddingProvider,
    SentenceTransformersProvider,
    BGEEmbeddingProvider,
    EmbeddingManager
)
from .cache import (
    MemoryCacheBackend,
    CachingEmbeddingProvider
)

# 向量存储
from .vector_stores import (
    FAISSVectorStore,
    ChromaVectorStore,
    InMemoryVectorStore
)

# 检索器和引擎
from .engine import (
    StandardRetriever,
    RAGEngine
)

# 模块信息
__version__ = "1.0.0"
__author__ = "Shrimp Agent Team"
__description__ = "RAG引擎 - 检索增强生成系统"

# 导出列表
__all__ = [
    # 枚举类型
    "DocumentType",
    "ChunkingStrategy",
    "EmbeddingModel",
    "VectorStoreType",
    "RetrievalStrategy",
    
    # 数据类
    "Document",
    "DocumentChunk",
    "RetrievalQuery",
    "RetrievalResult",
    "RAGResponse",
    
    # 异常类
    "RAGError",
    "DocumentProcessingError",
    "EmbeddingError",
    "RetrievalError",
    "VectorStoreError",
    
    # 基础接口
    "BaseDocumentProcessor",
    "BaseEmbeddingProvider",
    "BaseVectorStore",
    "BaseRetriever",
    "BaseRAGEngine",
    
    # 文档处理器
    "TextDocumentProcessor",
    "JSONDocumentProcessor",
    "HTMLDocumentProcessor",
    
    # 嵌入提供商
    "OpenAIEmbeddingProvider",
    "SentenceTransformersProvider",
    "BGEEmbeddingProvider",
    "EmbeddingManager",
    
    # 向量存储
    "FAISSVectorStore",
    "ChromaVectorStore",
    "InMemoryVectorStore",
    
    # 检索器和引擎
    "StandardRetriever",
    "RAGEngine",
    
    # 工厂函数
    "create_rag_engine",
    "create_document_processor",
    "create_embedding_provider",
    "create_vector_store",
    "create_retriever"
]


def create_document_processor(processor_type: str, config: dict) -> BaseDocumentProcessor:
    """创建文档处理器的工厂函数
    
    Args:
        processor_type: 处理器类型 ('text', 'json', 'html')
        config: 处理器配置
        
    Returns:
        文档处理器实例
        
    Raises:
        ValueError: 不支持的处理器类型
    """
    processors = {
        'text': TextDocumentProcessor,
        'json': JSONDocumentProcessor,
        'html': HTMLDocumentProcessor,
        'enhanced': EnhancedDocumentProcessor
    }
    
    if processor_type not in processors:
        raise ValueError(f"不支持的文档处理器类型: {processor_type}")
    
    return processors[processor_type](config)


def create_embedding_provider(model: EmbeddingModel, config: dict) -> BaseEmbeddingProvider:
    """创建嵌入提供商的工厂函数
    
    Args:
        model: 嵌入模型
        config: 提供商配置
        
    Returns:
        嵌入提供商实例
        
    Raises:
        ValueError: 不支持的模型类型
    """
    # 创建底层提供商
    if model in [EmbeddingModel.OPENAI_ADA, EmbeddingModel.OPENAI_3_SMALL, EmbeddingModel.OPENAI_3_LARGE]:
        provider = OpenAIEmbeddingProvider(model, config)
    elif model == EmbeddingModel.SENTENCE_TRANSFORMERS:
        provider = SentenceTransformersProvider(model, config)
    elif model in [EmbeddingModel.BGE_LARGE, EmbeddingModel.BGE_BASE]:
        provider = BGEEmbeddingProvider(model, config)
    else:
        raise ValueError(f"不支持的嵌入模型: {model}")

    # 可选缓存包装
    cache_cfg = config.get('cache', {}) if isinstance(config, dict) else {}
    if cache_cfg.get('enabled', False):
        backend_type = cache_cfg.get('backend', 'memory')
        if backend_type == 'memory':
            backend = MemoryCacheBackend(max_entries=cache_cfg.get('max_entries', 10000))
        else:
            # 未来可扩展磁盘/redis，当前回退到内存
            backend = MemoryCacheBackend(max_entries=cache_cfg.get('max_entries', 10000))
        provider = CachingEmbeddingProvider(provider, backend)

    return provider


def create_vector_store(store_type: VectorStoreType, config: dict) -> BaseVectorStore:
    """创建向量存储的工厂函数
    
    Args:
        store_type: 存储类型
        config: 存储配置
        
    Returns:
        向量存储实例
        
    Raises:
        ValueError: 不支持的存储类型
    """
    stores = {
        VectorStoreType.FAISS: FAISSVectorStore,
        VectorStoreType.CHROMA: ChromaVectorStore,
        'memory': InMemoryVectorStore  # 特殊类型
    }
    
    store_class = stores.get(store_type)
    if not store_class:
        raise ValueError(f"不支持的向量存储类型: {store_type}")
    
    return store_class(store_type, config)


def create_retriever(vector_store: BaseVectorStore, 
                    embedding_provider: BaseEmbeddingProvider,
                    config: dict) -> BaseRetriever:
    """创建检索器的工厂函数
    
    Args:
        vector_store: 向量存储
        embedding_provider: 嵌入提供商
        config: 检索器配置
        
    Returns:
        检索器实例
    """
    return StandardRetriever(vector_store, embedding_provider, config)


def create_rag_engine(config: dict) -> RAGEngine:
    """创建RAG引擎的工厂函数
    
    Args:
        config: RAG引擎配置
        
    Returns:
        RAG引擎实例
        
    Example:
        >>> config = {
        ...     'document_processor': {
        ...         'type': 'text',
        ...         'chunk_size': 1000,
        ...         'chunk_overlap': 200,
        ...         'strategy': 'fixed_size'
        ...     },
        ...     'embedding': {
        ...         'model': 'text-embedding-ada-002',
        ...         'api_key': 'your-api-key'
        ...     },
        ...     'vector_store': {
        ...         'type': 'faiss',
        ...         'dimension': 1536,
        ...         'index_path': './faiss_index'
        ...     },
        ...     'retriever': {
        ...         'default_top_k': 5,
        ...         'default_threshold': 0.7
        ...     },
        ...     'llm_manager': None  # 可选的LLM管理器
        ... }
        >>> engine = create_rag_engine(config)
    """
    # 创建文档处理器
    doc_processor_config = config.get('document_processor', {})
    doc_processor_type = doc_processor_config.get('type', 'text')
    document_processor = create_document_processor(doc_processor_type, doc_processor_config)
    
    # 创建嵌入提供商
    embedding_config = config.get('embedding', {})
    embedding_model = EmbeddingModel(embedding_config.get('model', 'text-embedding-ada-002'))
    embedding_provider = create_embedding_provider(embedding_model, embedding_config)
    
    # 创建向量存储
    vector_store_config = config.get('vector_store', {})
    vector_store_type = VectorStoreType(vector_store_config.get('type', 'faiss'))
    vector_store = create_vector_store(vector_store_type, vector_store_config)
    
    # 创建检索器
    retriever_config = config.get('retriever', {})
    retriever = create_retriever(vector_store, embedding_provider, retriever_config)
    
    # 创建RAG引擎
    engine_config = {
        'llm_manager': config.get('llm_manager'),
        'max_context_length': config.get('max_context_length', 4000),
        'answer_language': config.get('answer_language', 'zh-CN'),
        'include_sources': config.get('include_sources', True)
    }
    
    return RAGEngine(
        document_processor=document_processor,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        retriever=retriever,
        config=engine_config
    )


def get_default_config() -> dict:
    """获取默认RAG配置
    
    Returns:
        默认配置字典
    """
    return {
        'document_processor': {
            'type': 'enhanced',
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'strategy': 'fixed_size',
            'min_chunk_size': 100,
            'max_chunk_size': 2000,
            'dynamic_chunking': True
        },
        'embedding': {
            'model': 'text-embedding-ada-002',
            'api_key': '',
            'dimension': 1536,
            'batch_size': 100,
            'cache': {
                'enabled': True,
                'backend': 'memory',
                'max_entries': 10000,
                'ttl_seconds': 7 * 24 * 3600
            }
        },
        'vector_store': {
            'type': 'faiss',
            'dimension': 1536,
            'index_path': './faiss_index',
            'metadata_path': './faiss_metadata.db'
        },
        'retriever': {
            'default_top_k': 5,
            'default_threshold': 0.7,
            'enable_rerank': False,
            'query_expansion': False,
            'mmr_lambda': 0.5
        },
        'engine': {
            'max_context_length': 4000,
            'answer_language': 'zh-CN',
            'include_sources': True
        }
    }


def validate_config(config: dict) -> tuple[bool, list[str]]:
    """验证RAG配置
    
    Args:
        config: 待验证的配置
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    # 检查必需的配置节
    required_sections = ['document_processor', 'embedding', 'vector_store', 'retriever']
    for section in required_sections:
        if section not in config:
            errors.append(f"缺少配置节: {section}")
    
    # 验证文档处理器配置
    if 'document_processor' in config:
        doc_config = config['document_processor']
        if 'type' not in doc_config:
            errors.append("文档处理器缺少类型配置")
        elif doc_config['type'] not in ['text', 'json', 'html']:
            errors.append(f"不支持的文档处理器类型: {doc_config['type']}")
    
    # 验证嵌入配置
    if 'embedding' in config:
        emb_config = config['embedding']
        if 'model' not in emb_config:
            errors.append("嵌入配置缺少模型")
    
    # 验证向量存储配置
    if 'vector_store' in config:
        vs_config = config['vector_store']
        if 'type' not in vs_config:
            errors.append("向量存储缺少类型配置")
        if 'dimension' not in vs_config or vs_config['dimension'] <= 0:
            errors.append("向量存储维度配置无效")
    
    # 验证检索器配置
    if 'retriever' in config:
        ret_config = config['retriever']
        if 'default_top_k' in ret_config and ret_config['default_top_k'] <= 0:
            errors.append("检索器top_k配置无效")
        if 'default_threshold' in ret_config:
            threshold = ret_config['default_threshold']
            if not (0 <= threshold <= 1):
                errors.append("检索器阈值配置无效")
    
    return len(errors) == 0, errors


# 便捷的预配置创建函数
def create_simple_rag_engine(embedding_api_key: str = "", 
                            vector_store_path: str = "./rag_data") -> RAGEngine:
    """创建简单的RAG引擎
    
    Args:
        embedding_api_key: 嵌入API密钥
        vector_store_path: 向量存储路径
        
    Returns:
        配置好的RAG引擎
    """
    config = get_default_config()
    
    # 更新配置
    if embedding_api_key:
        config['embedding']['api_key'] = embedding_api_key
    
    config['vector_store']['index_path'] = vector_store_path
    config['vector_store']['metadata_path'] = f"{vector_store_path}/metadata.db"
    
    return create_rag_engine(config)


def create_memory_rag_engine() -> RAGEngine:
    """创建内存RAG引擎（用于测试）
    
    Returns:
        内存RAG引擎
    """
    config = get_default_config()
    
    # 使用内存存储
    config['vector_store'] = {
        'type': 'memory',
        'dimension': 384  # 使用较小的维度
    }
    
    # 使用本地嵌入模型
    config['embedding'] = {
        'model': 'sentence-transformers',
        'model_name': 'all-MiniLM-L6-v2',
        'dimension': 384
    }
    
    return create_rag_engine(config)