#!/usr/bin/env python3
"""
CAMEL框架智能体基础模块
基于CAMEL-AI框架的多智能体协作系统

运行环境: Python 3.11+
依赖: abc, typing, dataclasses, asyncio
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import json


class AgentRole(Enum):
    """CAMEL智能体角色枚举"""
    COORDINATOR = "coordinator"  # 协调代理
    SEARCHER = "searcher"       # 搜索代理
    EXTRACTOR = "extractor"     # 提取代理
    ANALYZER = "analyzer"       # 分析代理
    GENERATOR = "generator"     # 生成代理
    REVIEWER = "reviewer"       # 审查代理
    RESEARCHER = "researcher"   # 研究代理


class TaskType(Enum):
    """任务类型枚举"""
    SEARCH = "search"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    GENERATE = "generate"
    REVIEW = "review"
    COORDINATE = "coordinate"
    RESEARCH = "research"


class MessageType(Enum):
    """消息类型枚举"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    COLLABORATION = "collaboration"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"


@dataclass
class AgentMessage:
    """智能体间通信消息"""
    sender_id: str
    receiver_id: str
    message_type: MessageType
    content: Dict[str, Any]
    task_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message_type': self.message_type.value,
            'content': self.content,
            'task_id': self.task_id,
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id
        }


@dataclass
class AgentTool:
    """智能体工具定义"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)
    
    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        try:
            if asyncio.iscoroutinefunction(self.function):
                return await self.function(**kwargs)
            else:
                return self.function(**kwargs)
        except Exception as e:
            raise ToolExecutionError(f"Tool {self.name} execution failed: {str(e)}")


@dataclass
class AgentState:
    """智能体状态"""
    agent_id: str
    role: AgentRole
    status: str = "idle"  # idle, busy, error, offline
    current_task: Optional[str] = None
    memory: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_status(self, status: str, task_id: Optional[str] = None):
        """更新状态"""
        self.status = status
        self.current_task = task_id
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'agent_id': self.agent_id,
            'role': self.role.value,
            'status': self.status,
            'current_task': self.current_task,
            'memory': self.memory,
            'metrics': self.metrics,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class CAMELTask:
    """CAMEL任务定义"""
    task_id: str
    task_type: TaskType
    description: str
    input_data: Dict[str, Any]
    requirements: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    timeout: float = 300.0
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type.value,
            'description': self.description,
            'input_data': self.input_data,
            'requirements': self.requirements,
            'constraints': self.constraints,
            'priority': self.priority,
            'timeout': self.timeout,
            'dependencies': self.dependencies,
            'assigned_agent': self.assigned_agent,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class CAMELResult:
    """CAMEL任务结果"""
    task_id: str
    agent_id: str
    success: bool
    result_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    quality_score: float = 0.0
    completed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'agent_id': self.agent_id,
            'success': self.success,
            'result_data': self.result_data,
            'metadata': self.metadata,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'quality_score': self.quality_score,
            'completed_at': self.completed_at.isoformat()
        }


class BaseCAMELAgent(ABC):
    """CAMEL智能体基类
    
    基于CAMEL框架的角色扮演智能体
    支持工具调用、状态记忆、协作通信
    """
    
    def __init__(self, agent_id: str, role: AgentRole, config: Dict[str, Any]):
        """初始化CAMEL智能体
        
        Args:
            agent_id: 智能体唯一标识
            role: 智能体角色
            config: 配置参数
        """
        self.agent_id = agent_id
        self.role = role
        self.config = config
        self.state = AgentState(agent_id=agent_id, role=role)
        self.tools: Dict[str, AgentTool] = {}
        self.message_queue: List[AgentMessage] = []
        self.collaboration_history: List[Dict[str, Any]] = []
        self.llm_interface = config.get('llm_interface')
        
        # 角色特定的系统提示
        self.system_prompt = self._generate_system_prompt()
        
        # 注册工具
        self._register_tools()
        
        # 验证配置
        if not self.validate_config():
            raise ValueError(f"Invalid configuration for CAMEL agent {self.agent_id}")
    
    @abstractmethod
    def _generate_system_prompt(self) -> str:
        """生成角色特定的系统提示
        
        Returns:
            str: 系统提示
        """
        pass
    
    @abstractmethod
    def _register_tools(self) -> None:
        """注册智能体工具"""
        pass
    
    @abstractmethod
    async def process_task(self, task: CAMELTask) -> CAMELResult:
        """处理任务
        
        Args:
            task: CAMEL任务
            
        Returns:
            CAMELResult: 任务结果
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            bool: 配置是否有效
        """
        pass
    
    def register_tool(self, tool: AgentTool) -> None:
        """注册工具
        
        Args:
            tool: 智能体工具
        """
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[AgentTool]:
        """获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[AgentTool]: 工具实例
        """
        return self.tools.get(name)
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            Any: 工具执行结果
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ToolNotFoundError(f"Tool {tool_name} not found")
        
        return await tool.execute(**kwargs)
    
    async def send_message(self, receiver_id: str, message_type: MessageType, 
                          content: Dict[str, Any], task_id: str = "") -> None:
        """发送消息给其他智能体
        
        Args:
            receiver_id: 接收者ID
            message_type: 消息类型
            content: 消息内容
            task_id: 任务ID
        """
        message = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            task_id=task_id
        )
        
        # 这里应该通过消息总线发送，暂时存储到历史记录
        self.collaboration_history.append({
            'type': 'sent_message',
            'message': message.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
    
    async def receive_message(self, message: AgentMessage) -> None:
        """接收消息
        
        Args:
            message: 接收到的消息
        """
        self.message_queue.append(message)
        
        # 记录协作历史
        self.collaboration_history.append({
            'type': 'received_message',
            'message': message.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
        
        # 处理消息
        await self._handle_message(message)
    
    async def _handle_message(self, message: AgentMessage) -> None:
        """处理接收到的消息
        
        Args:
            message: 消息
        """
        if message.message_type == MessageType.TASK_REQUEST:
            # 处理任务请求
            await self._handle_task_request(message)
        elif message.message_type == MessageType.COLLABORATION:
            # 处理协作请求
            await self._handle_collaboration(message)
        elif message.message_type == MessageType.STATUS_UPDATE:
            # 处理状态更新
            await self._handle_status_update(message)
    
    async def _handle_task_request(self, message: AgentMessage) -> None:
        """处理任务请求"""
        # 子类实现具体逻辑
        pass
    
    async def _handle_collaboration(self, message: AgentMessage) -> None:
        """处理协作请求"""
        # 子类实现具体逻辑
        pass
    
    async def _handle_status_update(self, message: AgentMessage) -> None:
        """处理状态更新"""
        # 子类实现具体逻辑
        pass
    
    async def communicate_with_llm(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """与LLM通信
        
        Args:
            prompt: 提示词
            context: 上下文信息
            
        Returns:
            str: LLM响应
        """
        if not self.llm_interface:
            raise LLMNotAvailableError("LLM interface not configured")
        
        # 构建完整提示
        full_prompt = f"{self.system_prompt}\n\n{prompt}"
        
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            full_prompt += f"\n\n上下文信息:\n{context_str}"
        
        try:
            response = await self.llm_interface.generate_response(
                prompt=full_prompt,
                max_tokens=self.config.get('max_tokens', 1000),
                temperature=self.config.get('temperature', 0.7)
            )
            return response
        except Exception as e:
            raise LLMCommunicationError(f"LLM communication failed: {str(e)}")
    
    def update_memory(self, key: str, value: Any) -> None:
        """更新记忆
        
        Args:
            key: 记忆键
            value: 记忆值
        """
        self.state.memory[key] = value
        self.state.last_updated = datetime.now()
    
    def get_memory(self, key: str, default: Any = None) -> Any:
        """获取记忆
        
        Args:
            key: 记忆键
            default: 默认值
            
        Returns:
            Any: 记忆值
        """
        return self.state.memory.get(key, default)
    
    def get_state(self) -> AgentState:
        """获取智能体状态
        
        Returns:
            AgentState: 当前状态
        """
        return self.state
    
    def get_collaboration_history(self) -> List[Dict[str, Any]]:
        """获取协作历史
        
        Returns:
            List[Dict[str, Any]]: 协作历史
        """
        return self.collaboration_history
    
    def __str__(self) -> str:
        return f"CAMELAgent(id={self.agent_id}, role={self.role.value}, status={self.state.status})"
    
    def __repr__(self) -> str:
        return self.__str__()


# 异常类定义
class CAMELError(Exception):
    """CAMEL相关错误基类"""
    pass


class ToolExecutionError(CAMELError):
    """工具执行错误"""
    pass


class ToolNotFoundError(CAMELError):
    """工具未找到错误"""
    pass


class LLMNotAvailableError(CAMELError):
    """LLM不可用错误"""
    pass


class LLMCommunicationError(CAMELError):
    """LLM通信错误"""
    pass


class AgentCommunicationError(CAMELError):
    """智能体通信错误"""
    pass