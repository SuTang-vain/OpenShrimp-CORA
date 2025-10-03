#!/usr/bin/env python3
"""
搜索API数据模式
定义搜索相关的请求和响应数据结构

运行环境: Python 3.11+
依赖: pydantic, typing
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


class SearchStrategy(str, Enum):
    """搜索策略枚举"""
    SIMILARITY = "similarity"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    MMR = "mmr"
    SEMANTIC_HYBRID = "semantic_hybrid"


class SearchFilters(BaseModel):
    """搜索过滤器"""
    doc_type: Optional[str] = Field(None, description="文档类型")
    source: Optional[str] = Field(None, description="来源")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    language: Optional[str] = Field(None, description="语言")
    author: Optional[str] = Field(None, description="作者")
    custom_filters: Optional[Dict[str, Any]] = Field(None, description="自定义过滤器")
    
    class Config:
        schema_extra = {
            "example": {
                "doc_type": "pdf",
                "source": "research_papers",
                "date_from": "2023-01-01T00:00:00",
                "date_to": "2023-12-31T23:59:59",
                "tags": ["AI", "机器学习"],
                "language": "zh-CN",
                "author": "张三"
            }
        }


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1, max_length=1000, description="搜索查询")
    strategy: SearchStrategy = Field(default=SearchStrategy.SIMILARITY, description="搜索策略")
    top_k: int = Field(default=5, ge=1, le=50, description="返回结果数量")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")
    filters: Optional[SearchFilters] = Field(None, description="搜索过滤器")
    include_metadata: bool = Field(default=True, description="是否包含元数据")
    rerank: bool = Field(default=False, description="是否重新排序")
    expand_query: bool = Field(default=False, description="是否扩展查询")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('查询不能为空')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "query": "人工智能在医疗领域的应用",
                "strategy": "hybrid",
                "top_k": 10,
                "threshold": 0.75,
                "filters": {
                    "doc_type": "pdf",
                    "tags": ["AI", "医疗"]
                },
                "include_metadata": True,
                "rerank": True,
                "expand_query": False
            }
        }


class SearchResultItem(BaseModel):
    """搜索结果项"""
    content: str = Field(..., description="内容")
    score: float = Field(..., description="相似度分数")
    rank: int = Field(..., description="排名")
    doc_id: str = Field(..., description="文档ID")
    chunk_id: str = Field(..., description="文档块ID")
    source: Optional[str] = Field(None, description="来源")
    title: Optional[str] = Field(None, description="标题")
    url: Optional[str] = Field(None, description="URL")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    highlight: Optional[str] = Field(None, description="高亮片段")
    
    class Config:
        schema_extra = {
            "example": {
                "content": "人工智能在医疗诊断中发挥着重要作用...",
                "score": 0.85,
                "rank": 1,
                "doc_id": "doc_123",
                "chunk_id": "chunk_456",
                "source": "医学期刊",
                "title": "AI医疗应用研究",
                "url": "https://example.com/paper.pdf",
                "metadata": {
                    "author": "李医生",
                    "publish_date": "2023-06-15"
                },
                "highlight": "<mark>人工智能</mark>在<mark>医疗</mark>诊断中..."
            }
        }


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str = Field(..., description="原始查询")
    results: List[SearchResultItem] = Field(..., description="搜索结果")
    total_results: int = Field(..., description="结果总数")
    execution_time: float = Field(..., description="执行时间（秒）")
    strategy: SearchStrategy = Field(..., description="使用的搜索策略")
    metadata: Optional[Dict[str, Any]] = Field(None, description="响应元数据")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "人工智能在医疗领域的应用",
                "results": [
                    {
                        "content": "人工智能在医疗诊断中发挥着重要作用...",
                        "score": 0.85,
                        "rank": 1,
                        "doc_id": "doc_123",
                        "chunk_id": "chunk_456",
                        "source": "医学期刊",
                        "title": "AI医疗应用研究"
                    }
                ],
                "total_results": 1,
                "execution_time": 0.25,
                "strategy": "hybrid",
                "metadata": {
                    "user_id": "user_789",
                    "timestamp": 1640995200.0
                }
            }
        }


class RAGQueryRequest(BaseModel):
    """RAG查询请求"""
    query: str = Field(..., min_length=1, max_length=1000, description="查询问题")
    strategy: SearchStrategy = Field(default=SearchStrategy.SIMILARITY, description="检索策略")
    top_k: int = Field(default=5, ge=1, le=20, description="检索文档数量")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")
    filters: Optional[SearchFilters] = Field(None, description="检索过滤器")
    rerank: bool = Field(default=False, description="是否重新排序")
    expand_query: bool = Field(default=False, description="是否扩展查询")
    language: str = Field(default="zh-CN", description="回答语言")
    max_context_length: int = Field(default=4000, ge=1000, le=8000, description="最大上下文长度")
    include_sources: bool = Field(default=True, description="是否包含来源")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('查询不能为空')
        return v.strip()
    
    @validator('language')
    def validate_language(cls, v):
        allowed_languages = ['zh-CN', 'en-US', 'ja-JP', 'ko-KR']
        if v not in allowed_languages:
            raise ValueError(f'不支持的语言: {v}，支持的语言: {allowed_languages}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "query": "什么是深度学习？它有哪些应用？",
                "strategy": "hybrid",
                "top_k": 5,
                "threshold": 0.75,
                "filters": {
                    "doc_type": "pdf",
                    "tags": ["深度学习", "AI"]
                },
                "rerank": True,
                "expand_query": False,
                "language": "zh-CN",
                "max_context_length": 4000,
                "include_sources": True
            }
        }


class RetrievedChunk(BaseModel):
    """检索到的文档块"""
    content: str = Field(..., description="内容")
    score: float = Field(..., description="相似度分数")
    source: str = Field(..., description="来源")
    doc_id: str = Field(..., description="文档ID")
    chunk_id: str = Field(..., description="文档块ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    class Config:
        schema_extra = {
            "example": {
                "content": "深度学习是机器学习的一个分支...",
                "score": 0.92,
                "source": "AI教科书",
                "doc_id": "book_001",
                "chunk_id": "chapter_3_section_1",
                "metadata": {
                    "chapter": "第三章",
                    "page": 45
                }
            }
        }


class RAGQueryResponse(BaseModel):
    """RAG查询响应"""
    query: str = Field(..., description="原始查询")
    answer: str = Field(..., description="生成的答案")
    sources: List[str] = Field(..., description="信息来源")
    retrieved_chunks: List[RetrievedChunk] = Field(..., description="检索到的文档块")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    execution_time: float = Field(..., description="执行时间（秒）")
    metadata: Optional[Dict[str, Any]] = Field(None, description="响应元数据")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "什么是深度学习？它有哪些应用？",
                "answer": "深度学习是机器学习的一个分支，它使用多层神经网络来学习数据的复杂模式。主要应用包括：1. 计算机视觉 2. 自然语言处理 3. 语音识别 4. 推荐系统等。",
                "sources": ["AI教科书", "深度学习论文集"],
                "retrieved_chunks": [
                    {
                        "content": "深度学习是机器学习的一个分支...",
                        "score": 0.92,
                        "source": "AI教科书",
                        "doc_id": "book_001",
                        "chunk_id": "chapter_3_section_1"
                    }
                ],
                "confidence": 0.88,
                "execution_time": 1.25,
                "metadata": {
                    "chunks_retrieved": 5,
                    "model_used": "gpt-4",
                    "timestamp": 1640995200.0
                }
            }
        }


class StreamSearchChunk(BaseModel):
    """流式搜索响应块"""
    type: str = Field(..., description="响应类型")
    content: Optional[str] = Field(None, description="内容")
    data: Optional[Dict[str, Any]] = Field(None, description="数据")
    is_final: bool = Field(default=False, description="是否为最终块")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "answer_chunk",
                "content": "深度学习是机器学习的一个分支",
                "data": {
                    "chunk_index": 1,
                    "total_chunks": 5
                },
                "is_final": False
            }
        }


class StreamSearchResponse(BaseModel):
    """流式搜索响应"""
    chunks: List[StreamSearchChunk] = Field(..., description="响应块列表")
    
    class Config:
        schema_extra = {
            "example": {
                "chunks": [
                    {
                        "type": "retrieval",
                        "data": {
                            "chunks_found": 5,
                            "search_time": 0.15
                        },
                        "is_final": False
                    },
                    {
                        "type": "answer_chunk",
                        "content": "深度学习是机器学习的一个分支",
                        "is_final": False
                    },
                    {
                        "type": "final",
                        "data": {
                            "total_time": 1.25,
                            "confidence": 0.88
                        },
                        "is_final": True
                    }
                ]
            }
        }


class SearchSuggestion(BaseModel):
    """搜索建议"""
    text: str = Field(..., description="建议文本")
    score: float = Field(..., description="相关性分数")
    type: str = Field(..., description="建议类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "深度学习算法",
                "score": 0.85,
                "type": "query_completion",
                "metadata": {
                    "frequency": 156,
                    "last_used": "2023-12-01"
                }
            }
        }


class SearchHistoryItem(BaseModel):
    """搜索历史项"""
    query: str = Field(..., description="查询文本")
    timestamp: datetime = Field(..., description="查询时间")
    strategy: SearchStrategy = Field(..., description="搜索策略")
    results_count: int = Field(..., description="结果数量")
    execution_time: float = Field(..., description="执行时间")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="用户评分")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "机器学习基础",
                "timestamp": "2023-12-01T10:30:00",
                "strategy": "hybrid",
                "results_count": 8,
                "execution_time": 0.45,
                "user_rating": 4
            }
        }


class SearchStats(BaseModel):
    """搜索统计信息"""
    total_queries: int = Field(..., description="总查询数")
    successful_queries: int = Field(..., description="成功查询数")
    failed_queries: int = Field(..., description="失败查询数")
    avg_execution_time: float = Field(..., description="平均执行时间")
    avg_results_count: float = Field(..., description="平均结果数量")
    popular_strategies: Dict[str, int] = Field(..., description="热门策略统计")
    recent_queries: List[str] = Field(..., description="最近查询")
    
    class Config:
        schema_extra = {
            "example": {
                "total_queries": 1250,
                "successful_queries": 1180,
                "failed_queries": 70,
                "avg_execution_time": 0.65,
                "avg_results_count": 7.2,
                "popular_strategies": {
                    "hybrid": 650,
                    "similarity": 400,
                    "keyword": 200
                },
                "recent_queries": [
                    "深度学习",
                    "自然语言处理",
                    "计算机视觉"
                ]
            }
        }


class SearchFeedback(BaseModel):
    """搜索反馈"""
    query: str = Field(..., description="查询文本")
    rating: int = Field(..., ge=1, le=5, description="评分 (1-5)")
    feedback_type: str = Field(..., description="反馈类型")
    comments: Optional[str] = Field(None, max_length=1000, description="评论")
    helpful_results: Optional[List[str]] = Field(None, description="有用的结果ID")
    unhelpful_results: Optional[List[str]] = Field(None, description="无用的结果ID")
    suggestions: Optional[str] = Field(None, max_length=500, description="改进建议")
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        allowed_types = ['quality', 'relevance', 'speed', 'interface', 'other']
        if v not in allowed_types:
            raise ValueError(f'无效的反馈类型: {v}，允许的类型: {allowed_types}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "query": "机器学习算法",
                "rating": 4,
                "feedback_type": "relevance",
                "comments": "结果很相关，但希望有更多实际应用案例",
                "helpful_results": ["result_1", "result_3"],
                "unhelpful_results": ["result_5"],
                "suggestions": "增加更多实践案例"
            }
        }


class QueryAnalysis(BaseModel):
    """查询分析结果"""
    query: str = Field(..., description="原始查询")
    intent: str = Field(..., description="查询意图")
    keywords: List[str] = Field(..., description="关键词")
    entities: List[Dict[str, Any]] = Field(..., description="实体识别")
    complexity: str = Field(..., description="复杂度级别")
    language: str = Field(..., description="语言")
    suggested_strategy: SearchStrategy = Field(..., description="建议的搜索策略")
    confidence: float = Field(..., ge=0.0, le=1.0, description="分析置信度")
    
    @validator('intent')
    def validate_intent(cls, v):
        allowed_intents = [
            'factual', 'definition', 'comparison', 'how_to', 
            'explanation', 'list', 'opinion', 'other'
        ]
        if v not in allowed_intents:
            raise ValueError(f'无效的查询意图: {v}，允许的意图: {allowed_intents}')
        return v
    
    @validator('complexity')
    def validate_complexity(cls, v):
        allowed_levels = ['simple', 'medium', 'complex']
        if v not in allowed_levels:
            raise ValueError(f'无效的复杂度级别: {v}，允许的级别: {allowed_levels}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "query": "深度学习在医疗诊断中的应用原理",
                "intent": "explanation",
                "keywords": ["深度学习", "医疗诊断", "应用", "原理"],
                "entities": [
                    {"text": "深度学习", "type": "TECHNOLOGY"},
                    {"text": "医疗诊断", "type": "DOMAIN"}
                ],
                "complexity": "medium",
                "language": "zh-CN",
                "suggested_strategy": "hybrid",
                "confidence": 0.92
            }
        }