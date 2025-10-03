#!/usr/bin/env python3
"""
智能体服务管理器
管理智能体的生命周期和协调

运行环境: Python 3.11+
依赖: typing, asyncio
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentTask:
    """智能体任务"""
    task_id: str
    agent_type: str
    input_data: Dict[str, Any]
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class AgentServiceManager:
    """智能体服务管理器"""
    
    def __init__(self):
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Dict[str, AgentTask] = {}
        self.max_concurrent_tasks = 10
    
    async def create_task(self, agent_type: str, input_data: Dict[str, Any]) -> str:
        """创建智能体任务
        
        Args:
            agent_type: 智能体类型
            input_data: 输入数据
            
        Returns:
            任务ID
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        task = AgentTask(
            task_id=task_id,
            agent_type=agent_type,
            input_data=input_data
        )
        
        self.active_tasks[task_id] = task
        
        # 异步执行任务
        asyncio.create_task(self._execute_task(task))
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[AgentTask]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象或None
        """
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        elif task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        else:
            return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if task.status == "pending":
                task.status = "cancelled"
                task.completed_at = datetime.now()
                self.completed_tasks[task_id] = task
                del self.active_tasks[task_id]
                return True
        return False
    
    async def list_active_tasks(self) -> List[AgentTask]:
        """列出活跃任务
        
        Returns:
            活跃任务列表
        """
        return list(self.active_tasks.values())
    
    async def list_completed_tasks(self, limit: int = 100) -> List[AgentTask]:
        """列出已完成任务
        
        Args:
            limit: 返回数量限制
            
        Returns:
            已完成任务列表
        """
        tasks = list(self.completed_tasks.values())
        # 按完成时间倒序排列
        tasks.sort(key=lambda x: x.completed_at or datetime.min, reverse=True)
        return tasks[:limit]
    
    async def _execute_task(self, task: AgentTask):
        """执行任务
        
        Args:
            task: 任务对象
        """
        try:
            task.status = "running"
            task.started_at = datetime.now()
            
            # 模拟任务执行
            await asyncio.sleep(1)
            
            # 根据智能体类型执行不同逻辑
            if task.agent_type == "search":
                result = await self._execute_search_task(task.input_data)
            elif task.agent_type == "analysis":
                result = await self._execute_analysis_task(task.input_data)
            elif task.agent_type == "extraction":
                result = await self._execute_extraction_task(task.input_data)
            else:
                result = {"message": f"Unknown agent type: {task.agent_type}"}
            
            task.result = result
            task.status = "completed"
            
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
        
        finally:
            task.completed_at = datetime.now()
            
            # 移动到已完成任务
            if task.task_id in self.active_tasks:
                self.completed_tasks[task.task_id] = task
                del self.active_tasks[task.task_id]
    
    async def _execute_search_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行搜索任务
        
        Args:
            input_data: 输入数据
            
        Returns:
            搜索结果
        """
        query = input_data.get("query", "")
        
        # 模拟搜索逻辑
        await asyncio.sleep(2)
        
        return {
            "query": query,
            "results": [
                {"title": "搜索结果1", "content": "这是搜索结果1的内容"},
                {"title": "搜索结果2", "content": "这是搜索结果2的内容"}
            ],
            "total": 2
        }
    
    async def _execute_analysis_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析任务
        
        Args:
            input_data: 输入数据
            
        Returns:
            分析结果
        """
        content = input_data.get("content", "")
        
        # 模拟分析逻辑
        await asyncio.sleep(3)
        
        return {
            "content": content,
            "analysis": {
                "sentiment": "positive",
                "keywords": ["关键词1", "关键词2"],
                "summary": "这是内容的摘要"
            }
        }
    
    async def _execute_extraction_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行提取任务
        
        Args:
            input_data: 输入数据
            
        Returns:
            提取结果
        """
        url = input_data.get("url", "")
        
        # 模拟提取逻辑
        await asyncio.sleep(1.5)
        
        return {
            "url": url,
            "extracted_data": {
                "title": "提取的标题",
                "content": "提取的内容",
                "metadata": {"author": "作者", "date": "2024-01-01"}
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息
        """
        return {
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_status_breakdown": self._get_task_status_breakdown()
        }
    
    def _get_task_status_breakdown(self) -> Dict[str, int]:
        """获取任务状态分布
        
        Returns:
            状态分布字典
        """
        breakdown = {"pending": 0, "running": 0, "completed": 0, "failed": 0, "cancelled": 0}
        
        # 统计活跃任务
        for task in self.active_tasks.values():
            breakdown[task.status] = breakdown.get(task.status, 0) + 1
        
        # 统计已完成任务
        for task in self.completed_tasks.values():
            breakdown[task.status] = breakdown.get(task.status, 0) + 1
        
        return breakdown


# 全局实例
_agent_manager = None


def get_agent_manager() -> AgentServiceManager:
    """获取智能体管理器实例（单例模式）
    
    Returns:
        智能体管理器实例
    """
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentServiceManager()
    return _agent_manager