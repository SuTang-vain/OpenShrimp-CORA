#!/usr/bin/env python3
"""
智能体管理器
负责智能体的注册、管理和工作流执行

运行环境: Python 3.11+
依赖: asyncio, typing, logging
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field

from .base import BaseAgent, AgentContext, AgentResult


@dataclass
class WorkflowStep:
    """工作流步骤"""
    agent_name: str
    config_override: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[Callable[[AgentResult], bool]] = None
    retry_count: int = 0
    timeout: float = 300.0  # 5分钟超时


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    name: str
    description: str
    steps: List[WorkflowStep]
    parallel_execution: bool = False
    stop_on_failure: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowExecution:
    """工作流执行记录"""
    workflow_name: str
    context: AgentContext
    results: List[AgentResult] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class AgentManager:
    """智能体管理器
    
    负责智能体的注册、管理和工作流执行
    支持串行和并行执行模式
    """
    
    def __init__(self):
        """初始化管理器"""
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.logger = logging.getLogger(__name__)
        
        # 注册默认工作流
        self._register_default_workflows()
    
    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """注册智能体
        
        Args:
            name: 智能体名称
            agent: 智能体实例
        """
        if name in self.agents:
            self.logger.warning(f"Agent {name} already registered, overwriting")
        
        self.agents[name] = agent
        self.logger.info(f"Registered agent: {name}")
    
    def unregister_agent(self, name: str) -> bool:
        """注销智能体
        
        Args:
            name: 智能体名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self.agents:
            del self.agents[name]
            self.logger.info(f"Unregistered agent: {name}")
            return True
        return False
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取智能体
        
        Args:
            name: 智能体名称
            
        Returns:
            Optional[BaseAgent]: 智能体实例
        """
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """列出所有已注册的智能体
        
        Returns:
            List[str]: 智能体名称列表
        """
        return list(self.agents.keys())
    
    def create_workflow(self, definition: WorkflowDefinition) -> None:
        """创建工作流
        
        Args:
            definition: 工作流定义
        """
        # 验证工作流中的智能体是否都已注册
        for step in definition.steps:
            if step.agent_name not in self.agents:
                raise ValueError(f"Agent {step.agent_name} not registered")
        
        self.workflows[definition.name] = definition
        self.logger.info(f"Created workflow: {definition.name}")
    
    def get_workflow(self, name: str) -> Optional[WorkflowDefinition]:
        """获取工作流定义
        
        Args:
            name: 工作流名称
            
        Returns:
            Optional[WorkflowDefinition]: 工作流定义
        """
        return self.workflows.get(name)
    
    def list_workflows(self) -> List[str]:
        """列出所有工作流
        
        Returns:
            List[str]: 工作流名称列表
        """
        return list(self.workflows.keys())
    
    async def execute_workflow(self, workflow_name: str, context: AgentContext) -> WorkflowExecution:
        """执行工作流
        
        Args:
            workflow_name: 工作流名称
            context: 执行上下文
            
        Returns:
            WorkflowExecution: 执行记录
        """
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow {workflow_name} not found")
        
        execution = WorkflowExecution(
            workflow_name=workflow_name,
            context=context,
            started_at=datetime.now(),
            status="running"
        )
        
        self.executions[context.task_id] = execution
        
        try:
            if workflow.parallel_execution:
                results = await self._execute_parallel(workflow, context)
            else:
                results = await self._execute_sequential(workflow, context)
            
            execution.results = results
            execution.status = "completed"
            execution.completed_at = datetime.now()
            
        except Exception as e:
            execution.error = str(e)
            execution.status = "failed"
            execution.completed_at = datetime.now()
            self.logger.error(f"Workflow {workflow_name} failed: {e}")
        
        return execution
    
    async def _execute_sequential(self, workflow: WorkflowDefinition, context: AgentContext) -> List[AgentResult]:
        """串行执行工作流
        
        Args:
            workflow: 工作流定义
            context: 执行上下文
            
        Returns:
            List[AgentResult]: 执行结果列表
        """
        results = []
        
        for step in workflow.steps:
            agent = self.agents[step.agent_name]
            
            # 合并配置
            step_context = AgentContext(
                task_id=context.task_id,
                user_input=context.user_input,
                config={**context.config, **step.config_override},
                metadata=context.metadata
            )
            
            try:
                # 执行智能体任务
                result = await asyncio.wait_for(
                    agent._execute_with_metrics(step_context),
                    timeout=step.timeout
                )
                
                results.append(result)
                
                # 检查条件
                if step.condition and not step.condition(result):
                    self.logger.info(f"Step condition failed for {step.agent_name}")
                    break
                
                # 检查是否失败且需要停止
                if not result.success and workflow.stop_on_failure:
                    self.logger.error(f"Agent {step.agent_name} failed, stopping workflow")
                    break
                    
            except asyncio.TimeoutError:
                error_result = AgentResult(
                    success=False,
                    content="",
                    error=f"Agent {step.agent_name} timed out after {step.timeout}s",
                    metadata={'agent_name': step.agent_name}
                )
                results.append(error_result)
                
                if workflow.stop_on_failure:
                    break
        
        return results
    
    async def _execute_parallel(self, workflow: WorkflowDefinition, context: AgentContext) -> List[AgentResult]:
        """并行执行工作流
        
        Args:
            workflow: 工作流定义
            context: 执行上下文
            
        Returns:
            List[AgentResult]: 执行结果列表
        """
        tasks = []
        
        for step in workflow.steps:
            agent = self.agents[step.agent_name]
            
            # 合并配置
            step_context = AgentContext(
                task_id=context.task_id,
                user_input=context.user_input,
                config={**context.config, **step.config_override},
                metadata=context.metadata
            )
            
            # 创建任务
            task = asyncio.create_task(
                asyncio.wait_for(
                    agent._execute_with_metrics(step_context),
                    timeout=step.timeout
                )
            )
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = AgentResult(
                    success=False,
                    content="",
                    error=str(result),
                    metadata={'agent_name': workflow.steps[i].agent_name}
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_execution(self, task_id: str) -> Optional[WorkflowExecution]:
        """获取执行记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[WorkflowExecution]: 执行记录
        """
        return self.executions.get(task_id)
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """获取所有智能体的统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            name: agent.get_stats()
            for name, agent in self.agents.items()
        }
    
    def _register_default_workflows(self) -> None:
        """注册默认工作流"""
        # 简单搜索工作流
        simple_search = WorkflowDefinition(
            name="simple_search",
            description="简单搜索工作流",
            steps=[
                WorkflowStep(agent_name="analyzer"),
                WorkflowStep(agent_name="searcher"),
                WorkflowStep(agent_name="generator")
            ]
        )
        
        # 深度分析工作流
        deep_analysis = WorkflowDefinition(
            name="deep_analysis",
            description="深度分析工作流",
            steps=[
                WorkflowStep(agent_name="analyzer"),
                WorkflowStep(agent_name="researcher"),
                WorkflowStep(agent_name="reviewer"),
                WorkflowStep(agent_name="generator")
            ]
        )
        
        # 注意：这些工作流需要对应的智能体注册后才能使用
        # 这里只是预定义，实际使用时需要确保智能体已注册