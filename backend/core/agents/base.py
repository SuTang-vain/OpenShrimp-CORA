#!/usr/bin/env python3
"""
智能体引擎基础模块
提供智能体的基础抽象类和数据结构

运行环境: Python 3.11+
依赖: dataclasses, typing, abc, asyncio
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import uuid


@dataclass
class AgentContext:
    """智能体执行上下文"""
    task_id: str
    user_input: str
    config: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'user_input': self.user_input,
            'config': self.config,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class AgentResult:
    """智能体执行结果"""
    success: bool
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'success': self.success,
            'content': self.content,
            'metadata': self.metadata,
            'metrics': self.metrics,
            'error': self.error,
            'execution_time': self.execution_time,
            'created_at': self.created_at.isoformat()
        }


class BaseAgent(ABC):
    """智能体基类
    
    所有智能体都必须继承此基类并实现抽象方法
    提供统一的接口和基础功能
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化智能体
        
        Args:
            config: 智能体配置参数
        """
        self.config = config
        self.name = self.__class__.__name__
        self.agent_id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.execution_count = 0
        self.total_execution_time = 0.0
        
        # 验证配置
        if not self.validate_config():
            raise ValueError(f"Invalid configuration for agent {self.name}")
    
    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """执行智能体任务
        
        Args:
            context: 执行上下文
            
        Returns:
            AgentResult: 执行结果
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            bool: 配置是否有效
        """
        pass
    
    async def _execute_with_metrics(self, context: AgentContext) -> AgentResult:
        """带性能监控的执行方法
        
        Args:
            context: 执行上下文
            
        Returns:
            AgentResult: 执行结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await self.execute(context)
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # 更新统计信息
            self.execution_count += 1
            self.total_execution_time += execution_time
            result.execution_time = execution_time
            
            # 添加智能体信息到元数据
            result.metadata.update({
                'agent_name': self.name,
                'agent_id': self.agent_id,
                'execution_count': self.execution_count
            })
            
            return result
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return AgentResult(
                success=False,
                content="",
                error=str(e),
                execution_time=execution_time,
                metadata={
                    'agent_name': self.name,
                    'agent_id': self.agent_id,
                    'execution_count': self.execution_count
                }
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取智能体统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        avg_execution_time = (
            self.total_execution_time / self.execution_count 
            if self.execution_count > 0 else 0.0
        )
        
        return {
            'name': self.name,
            'agent_id': self.agent_id,
            'created_at': self.created_at.isoformat(),
            'execution_count': self.execution_count,
            'total_execution_time': self.total_execution_time,
            'average_execution_time': avg_execution_time
        }
    
    def __str__(self) -> str:
        return f"{self.name}(id={self.agent_id[:8]}, executions={self.execution_count})"
    
    def __repr__(self) -> str:
        return self.__str__()


class AgentCapability:
    """智能体能力描述"""
    
    def __init__(self, name: str, description: str, required_config: List[str]):
        self.name = name
        self.description = description
        self.required_config = required_config
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置是否满足能力要求"""
        return all(key in config for key in self.required_config)