#!/usr/bin/env python3
"""
嵌入与检索缓存封装
提供统一的缓存接口与带指标的嵌入缓存包装器

运行环境: Python 3.11+
依赖: typing, time, hashlib
"""

import time
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    evictions: int = 0
    total_requests: int = 0
    total_latency_saved_ms: float = 0.0
    last_reset_ts: float = field(default_factory=lambda: time.time())

    def snapshot(self) -> Dict[str, Any]:
        hit_rate = (self.hits / self.total_requests) if self.total_requests > 0 else 0.0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'evictions': self.evictions,
            'total_requests': self.total_requests,
            'hit_rate': hit_rate,
            'total_latency_saved_ms': self.total_latency_saved_ms,
            'last_reset_ts': self.last_reset_ts
        }


class ICacheBackend:
    """缓存后端接口"""
    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

    def get_stats(self) -> Dict[str, Any]:
        raise NotImplementedError


class MemoryCacheBackend(ICacheBackend):
    """简单的内存LRU缓存后端（近似实现）"""

    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._order: List[str] = []
        self._stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        self._stats.total_requests += 1
        item = self._store.get(key)
        if item is None:
            self._stats.misses += 1
            return None
        # 触发近似LRU更新
        try:
            self._order.remove(key)
        except ValueError:
            pass
        self._order.append(key)
        self._stats.hits += 1
        return item[0]

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        # ttl先忽略，后续可扩展
        if key not in self._store and len(self._order) >= self.max_entries:
            # 淘汰最久未使用项
            evict_key = self._order.pop(0)
            if evict_key in self._store:
                del self._store[evict_key]
                self._stats.evictions += 1

        self._store[key] = (value, time.time())
        try:
            self._order.remove(key)
        except ValueError:
            pass
        self._order.append(key)
        self._stats.sets += 1

    def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]
        try:
            self._order.remove(key)
        except ValueError:
            pass

    def clear(self) -> None:
        self._store.clear()
        self._order.clear()
        self._stats = CacheStats()

    def get_stats(self) -> Dict[str, Any]:
        return self._stats.snapshot()


def _hash_text(text: str, model_id: str) -> str:
    m = hashlib.sha256()
    # 限制长度避免超长文本影响性能
    truncated = text[:10000]
    m.update(truncated.encode('utf-8'))
    m.update(model_id.encode('utf-8'))
    return m.hexdigest()


class CachingEmbeddingProvider:
    """嵌入缓存包装器

    包装实际的嵌入提供商，提供单条与批量嵌入的缓存。
    统计命中率与节省的延迟，用于在RAG统计中暴露指标。
    """

    def __init__(self, provider, cache_backend: ICacheBackend):
        # provider需实现BaseEmbeddingProvider接口
        self.provider = provider
        self.cache = cache_backend
        self._stats = CacheStats()

        # 透传必要属性
        self.model = getattr(provider, 'model', None)
        self.config = getattr(provider, 'config', {})
        self.dimension = getattr(provider, 'dimension', 1536)

    async def embed_text(self, text: str) -> List[float]:
        model_id = self.model.value if hasattr(self.model, 'value') else str(self.model)
        key = f"emb:{model_id}:{_hash_text(text, model_id)}"

        # 命中则返回
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        # 记录开始时间，用于估算节省的延迟
        start_ms = time.time() * 1000
        vec = await self.provider.embed_text(text)
        end_ms = time.time() * 1000

        # 写入缓存并更新统计（以一次miss的真实耗时计入未来命中节省）
        self.cache.set(key, vec)
        self._stats.misses += 1
        self._stats.total_requests += 1
        self._stats.total_latency_saved_ms += max(0.0, end_ms - start_ms)
        return vec

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        model_id = self.model.value if hasattr(self.model, 'value') else str(self.model)
        keys = [f"emb:{model_id}:{_hash_text(t, model_id)}" for t in texts]

        results: List[Optional[List[float]]] = []
        missing_indices: List[int] = []

        # 先尝试命中缓存
        for i, key in enumerate(keys):
            cached = self.cache.get(key)
            if cached is not None:
                results.append(cached)
            else:
                results.append(None)
                missing_indices.append(i)

        # 对缺失项调用底层提供商
        if missing_indices:
            start_ms = time.time() * 1000
            batch_texts = [texts[i] for i in missing_indices]
            batch_vecs = await self.provider.embed_batch(batch_texts)
            end_ms = time.time() * 1000

            # 写入缓存并填充结果
            for j, idx in enumerate(missing_indices):
                key = keys[idx]
                vec = batch_vecs[j]
                self.cache.set(key, vec)
                results[idx] = vec

            # 更新统计
            self._stats.misses += len(missing_indices)
            self._stats.hits += (len(texts) - len(missing_indices))
            self._stats.total_requests += len(texts)
            self._stats.total_latency_saved_ms += max(0.0, end_ms - start_ms)

        else:
            # 全部命中
            self._stats.hits += len(texts)
            self._stats.total_requests += len(texts)

        # 类型校正
        return [r if r is not None else [] for r in results]

    def validate_config(self) -> bool:
        # 透传
        return getattr(self.provider, 'validate_config', lambda: True)()

    async def health_check(self) -> bool:
        # 透传
        return await getattr(self.provider, 'health_check')()

    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            'provider': self.provider.__class__.__name__,
            'backend': self.cache.__class__.__name__,
            'cache': self.cache.get_stats(),
            'wrapper': self._stats.snapshot()
        }