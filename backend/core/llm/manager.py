#!/usr/bin/env python3
"""
LLM管理器
统一管理多个LLM提供商和模型

运行环境: Python 3.11+
依赖: asyncio, typing, json
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from datetime import datetime
from enum import Enum

from .base import (
    BaseLLMProvider, ModelType, ProviderType,
    ModelInfo, LLMRequest, LLMResponse, StreamChunk, TokenUsage,
    LLMError, ModelNotFoundError, ProviderUnavailableError
)
from .providers import (
    OpenAIProvider, AnthropicProvider, GoogleProvider, LocalProvider
)


class LoadBalanceStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"  # 轮询
    RANDOM = "random"  # 随机
    LEAST_LOADED = "least_loaded"  # 最少负载
    FASTEST = "fastest"  # 最快响应
    CHEAPEST = "cheapest"  # 最便宜


class LLMManager:
    """LLM管理器
    
    统一管理多个LLM提供商，提供负载均衡、故障转移等功能
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers: Dict[ProviderType, BaseLLMProvider] = {}
        self.provider_stats: Dict[ProviderType, Dict[str, Any]] = {}
        self.load_balance_strategy = LoadBalanceStrategy(config.get('load_balance_strategy', 'round_robin'))
        self.enable_fallback = config.get('enable_fallback', True)
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 30.0)
        
        # 初始化提供商
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """初始化LLM提供商"""
        provider_configs = self.config.get('providers', {})
        
        for provider_name, provider_config in provider_configs.items():
            if not provider_config.get('enabled', False):
                continue
            
            try:
                provider_type = ProviderType(provider_name.lower())
                
                if provider_type == ProviderType.OPENAI:
                    provider = OpenAIProvider(provider_config)
                elif provider_type == ProviderType.ANTHROPIC:
                    provider = AnthropicProvider(provider_config)
                elif provider_type == ProviderType.GOOGLE:
                    provider = GoogleProvider(provider_config)
                elif provider_type == ProviderType.LOCAL:
                    provider = LocalProvider(provider_config)
                else:
                    continue
                
                if provider.validate_config():
                    self.providers[provider_type] = provider
                    self.provider_stats[provider_type] = {
                        'total_requests': 0,
                        'successful_requests': 0,
                        'failed_requests': 0,
                        'total_tokens': 0,
                        'total_cost': 0.0,
                        'avg_response_time': 0.0,
                        'last_used': None,
                        'health_status': True
                    }
                    
            except Exception as e:
                print(f"初始化提供商 {provider_name} 失败: {e}")
    
    async def generate(self, request: LLMRequest, 
                      preferred_provider: Optional[ProviderType] = None) -> LLMResponse:
        """生成响应
        
        Args:
            request: LLM请求
            preferred_provider: 首选提供商
            
        Returns:
            LLM响应
        """
        providers_to_try = self._get_providers_for_request(request, preferred_provider)
        
        last_error = None
        
        for provider_type in providers_to_try:
            provider = self.providers.get(provider_type)
            if not provider:
                continue
            
            try:
                # 更新统计
                self.provider_stats[provider_type]['total_requests'] += 1
                self.provider_stats[provider_type]['last_used'] = datetime.now().isoformat()
                
                # 执行请求
                response = await asyncio.wait_for(
                    provider.generate(request),
                    timeout=self.timeout
                )
                
                # 更新成功统计
                self._update_success_stats(provider_type, response)
                
                return response
                
            except Exception as e:
                last_error = e
                self._update_failure_stats(provider_type, e)
                
                if not self.enable_fallback:
                    break
                
                continue
        
        # 所有提供商都失败
        if last_error:
            raise last_error
        else:
            raise LLMError("没有可用的LLM提供商")
    
    async def generate_stream(self, request: LLMRequest,
                            preferred_provider: Optional[ProviderType] = None) -> AsyncGenerator[StreamChunk, None]:
        """流式生成响应
        
        Args:
            request: LLM请求
            preferred_provider: 首选提供商
            
        Yields:
            流式响应块
        """
        providers_to_try = self._get_providers_for_request(request, preferred_provider)
        
        last_error = None
        
        for provider_type in providers_to_try:
            provider = self.providers.get(provider_type)
            if not provider:
                continue
            
            try:
                # 更新统计
                self.provider_stats[provider_type]['total_requests'] += 1
                self.provider_stats[provider_type]['last_used'] = datetime.now().isoformat()
                
                # 执行流式请求
                async for chunk in provider.generate_stream(request):
                    yield chunk
                
                # 更新成功统计（简化版）
                self.provider_stats[provider_type]['successful_requests'] += 1
                
                return
                
            except Exception as e:
                last_error = e
                self._update_failure_stats(provider_type, e)
                
                if not self.enable_fallback:
                    break
                
                continue
        
        # 所有提供商都失败
        if last_error:
            raise last_error
        else:
            raise LLMError("没有可用的LLM提供商")
    
    async def list_models(self, provider_type: Optional[ProviderType] = None) -> List[ModelInfo]:
        """列出可用模型
        
        Args:
            provider_type: 指定提供商类型，None表示所有提供商
            
        Returns:
            模型信息列表
        """
        models = []
        
        if provider_type:
            provider = self.providers.get(provider_type)
            if provider:
                models.extend(await provider.list_models())
        else:
            for provider in self.providers.values():
                models.extend(await provider.list_models())
        
        return models
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型信息
        """
        for provider in self.providers.values():
            model_info = await provider.get_model_info(model_id)
            if model_info:
                return model_info
        
        return None
    
    async def health_check(self) -> Dict[ProviderType, bool]:
        """健康检查
        
        Returns:
            各提供商的健康状态
        """
        health_status = {}
        
        for provider_type, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                health_status[provider_type] = is_healthy
                self.provider_stats[provider_type]['health_status'] = is_healthy
            except Exception:
                health_status[provider_type] = False
                self.provider_stats[provider_type]['health_status'] = False
        
        return health_status
    
    def get_provider_stats(self) -> Dict[ProviderType, Dict[str, Any]]:
        """获取提供商统计信息
        
        Returns:
            提供商统计信息
        """
        return self.provider_stats.copy()
    
    def get_available_providers(self) -> List[ProviderType]:
        """获取可用提供商列表
        
        Returns:
            可用提供商类型列表
        """
        return [provider_type for provider_type, stats in self.provider_stats.items() 
                if stats.get('health_status', False)]
    
    def _get_providers_for_request(self, request: LLMRequest, 
                                 preferred_provider: Optional[ProviderType] = None) -> List[ProviderType]:
        """获取请求的提供商列表
        
        Args:
            request: LLM请求
            preferred_provider: 首选提供商
            
        Returns:
            按优先级排序的提供商列表
        """
        available_providers = []
        
        # 找到支持该模型的提供商
        for provider_type, provider in self.providers.items():
            if not self.provider_stats[provider_type].get('health_status', False):
                continue
            
            # 检查是否支持该模型
            if asyncio.run(provider.get_model_info(request.model)):
                available_providers.append(provider_type)
        
        if not available_providers:
            return []
        
        # 如果指定了首选提供商，优先使用
        if preferred_provider and preferred_provider in available_providers:
            providers_to_try = [preferred_provider]
            providers_to_try.extend([p for p in available_providers if p != preferred_provider])
            return providers_to_try
        
        # 根据负载均衡策略排序
        return self._sort_providers_by_strategy(available_providers)
    
    def _sort_providers_by_strategy(self, providers: List[ProviderType]) -> List[ProviderType]:
        """根据负载均衡策略排序提供商
        
        Args:
            providers: 可用提供商列表
            
        Returns:
            排序后的提供商列表
        """
        if self.load_balance_strategy == LoadBalanceStrategy.ROUND_ROBIN:
            # 简单轮询：按上次使用时间排序
            return sorted(providers, key=lambda p: self.provider_stats[p].get('last_used', '0'))
        
        elif self.load_balance_strategy == LoadBalanceStrategy.LEAST_LOADED:
            # 最少负载：按当前请求数排序
            return sorted(providers, key=lambda p: self.provider_stats[p]['total_requests'])
        
        elif self.load_balance_strategy == LoadBalanceStrategy.FASTEST:
            # 最快响应：按平均响应时间排序
            return sorted(providers, key=lambda p: self.provider_stats[p]['avg_response_time'])
        
        elif self.load_balance_strategy == LoadBalanceStrategy.CHEAPEST:
            # 最便宜：按总成本排序
            return sorted(providers, key=lambda p: self.provider_stats[p]['total_cost'])
        
        else:
            # 默认随机
            import random
            random.shuffle(providers)
            return providers
    
    def _update_success_stats(self, provider_type: ProviderType, response: LLMResponse) -> None:
        """更新成功统计
        
        Args:
            provider_type: 提供商类型
            response: LLM响应
        """
        stats = self.provider_stats[provider_type]
        stats['successful_requests'] += 1
        
        # 更新token统计
        if response.token_usage:
            stats['total_tokens'] += response.token_usage.total_tokens
        
        # 更新响应时间
        if response.execution_time:
            current_avg = stats['avg_response_time']
            total_requests = stats['successful_requests']
            stats['avg_response_time'] = (
                (current_avg * (total_requests - 1) + response.execution_time) / total_requests
            )
        
        # 更新成本（如果有模型信息）
        if response.token_usage:
            model_info = asyncio.run(self.providers[provider_type].get_model_info(response.model))
            if model_info and model_info.cost_per_1k_tokens:
                input_cost = (response.token_usage.input_tokens / 1000) * model_info.cost_per_1k_tokens.get('input', 0)
                output_cost = (response.token_usage.output_tokens / 1000) * model_info.cost_per_1k_tokens.get('output', 0)
                stats['total_cost'] += input_cost + output_cost
    
    def _update_failure_stats(self, provider_type: ProviderType, error: Exception) -> None:
        """更新失败统计
        
        Args:
            provider_type: 提供商类型
            error: 错误信息
        """
        stats = self.provider_stats[provider_type]
        stats['failed_requests'] += 1
        
        # 如果是严重错误，标记为不健康
        if isinstance(error, (ConnectionError, TimeoutError)):
            stats['health_status'] = False
    
    async def add_provider(self, provider_type: ProviderType, config: Dict[str, Any]) -> bool:
        """动态添加提供商
        
        Args:
            provider_type: 提供商类型
            config: 提供商配置
            
        Returns:
            是否添加成功
        """
        try:
            if provider_type == ProviderType.OPENAI:
                provider = OpenAIProvider(config)
            elif provider_type == ProviderType.ANTHROPIC:
                provider = AnthropicProvider(config)
            elif provider_type == ProviderType.GOOGLE:
                provider = GoogleProvider(config)
            elif provider_type == ProviderType.LOCAL:
                provider = LocalProvider(config)
            else:
                return False
            
            if provider.validate_config():
                self.providers[provider_type] = provider
                self.provider_stats[provider_type] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'avg_response_time': 0.0,
                    'last_used': None,
                    'health_status': True
                }
                return True
            
        except Exception as e:
            print(f"添加提供商 {provider_type} 失败: {e}")
        
        return False
    
    def remove_provider(self, provider_type: ProviderType) -> bool:
        """移除提供商
        
        Args:
            provider_type: 提供商类型
            
        Returns:
            是否移除成功
        """
        if provider_type in self.providers:
            del self.providers[provider_type]
            del self.provider_stats[provider_type]
            return True
        return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            配置信息
        """
        return {
            'load_balance_strategy': self.load_balance_strategy.value,
            'enable_fallback': self.enable_fallback,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'providers': list(self.providers.keys()),
            'total_providers': len(self.providers)
        }
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """更新配置
        
        Args:
            config: 新配置
        """
        if 'load_balance_strategy' in config:
            self.load_balance_strategy = LoadBalanceStrategy(config['load_balance_strategy'])
        
        if 'enable_fallback' in config:
            self.enable_fallback = config['enable_fallback']
        
        if 'max_retries' in config:
            self.max_retries = config['max_retries']
        
        if 'timeout' in config:
            self.timeout = config['timeout']