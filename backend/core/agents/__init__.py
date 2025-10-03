#!/usr/bin/env python3
"""
智能体模块初始化文件
导出核心智能体类和接口

运行环境: Python 3.11+
依赖: typing
"""

# 基础智能体类
from .base import (
    BaseAgent,
    AgentContext,
    AgentResult,
    AgentCapability
)

# 智能体管理器
from .manager import (
    AgentManager,
    WorkflowStep,
    WorkflowDefinition,
    WorkflowExecution
)

# 具体智能体实现
from .implementations import (
    AnalyzerAgent,
    SearcherAgent,
    ReviewerAgent,
    GeneratorAgent
)

# CAMEL框架智能体
from .camel_base import (
    BaseCAMELAgent,
    AgentRole,
    TaskType,
    MessageType,
    CAMELTask,
    CAMELResult,
    AgentMessage,
    AgentTool,
    AgentState
)

from .camel_agents import (
    CoordinatorAgent,
    SearcherAgent as CAMELSearcherAgent,
    ExtractorAgent,
    AnalyzerAgent as CAMELAnalyzerAgent
)

# 模块信息
__version__ = "1.0.0"
__author__ = "Shrimp Agent Team"
__description__ = "智能体引擎核心模块 - 支持CAMEL框架"

# 导出列表
__all__ = [
    # 基础类
    "BaseAgent",
    "AgentContext",
    "AgentResult",
    "AgentCapability",
    
    # 管理器
    "AgentManager",
    "WorkflowStep",
    "WorkflowDefinition",
    "WorkflowExecution",
    
    # 具体实现
    "AnalyzerAgent",
    "SearcherAgent",
    "ReviewerAgent",
    "GeneratorAgent",
    
    # CAMEL框架
    "BaseCAMELAgent",
    "AgentRole",
    "TaskType",
    "MessageType",
    "CAMELTask",
    "CAMELResult",
    "AgentMessage",
    "AgentTool",
    "AgentState",
    "CoordinatorAgent",
    "CAMELSearcherAgent",
    "ExtractorAgent",
    "CAMELAnalyzerAgent"
]