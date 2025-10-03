#!/usr/bin/env python3
"""
CAMEL框架智能体具体实现
基于CAMEL-AI框架的角色扮演智能体

运行环境: Python 3.11+
依赖: asyncio, typing, json
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .camel_base import (
    BaseCAMELAgent, AgentRole, TaskType, MessageType,
    CAMELTask, CAMELResult, AgentTool, AgentMessage
)


class CoordinatorAgent(BaseCAMELAgent):
    """协调代理
    
    负责任务分解、智能体协调和结果聚合
    基于CAMEL框架的协调者角色
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentRole.COORDINATOR, config)
    
    def _generate_system_prompt(self) -> str:
        """生成协调代理的系统提示"""
        return """
你是一个智能协调代理，负责多智能体系统的任务分解和协调。

你的职责包括：
1. 分析用户请求，将复杂任务分解为子任务
2. 根据任务特点选择合适的智能体
3. 协调各智能体的工作流程
4. 监控任务执行进度
5. 聚合和整合各智能体的结果
6. 处理异常情况和冲突解决

工作原则：
- 确保任务分解合理且高效
- 优化智能体间的协作流程
- 保证结果质量和一致性
- 及时处理异常和错误

请始终以JSON格式返回结构化的协调决策。
"""
    
    def _register_tools(self) -> None:
        """注册协调代理工具"""
        # 任务分解工具
        self.register_tool(AgentTool(
            name="task_decomposition",
            description="将复杂任务分解为子任务",
            function=self._decompose_task
        ))
        
        # 智能体选择工具
        self.register_tool(AgentTool(
            name="agent_selection",
            description="为任务选择合适的智能体",
            function=self._select_agents
        ))
        
        # 结果聚合工具
        self.register_tool(AgentTool(
            name="result_aggregation",
            description="聚合多个智能体的结果",
            function=self._aggregate_results
        ))
    
    def validate_config(self) -> bool:
        """验证配置"""
        required_keys = ['available_agents', 'max_subtasks']
        return all(key in self.config for key in required_keys)
    
    async def process_task(self, task: CAMELTask) -> CAMELResult:
        """处理协调任务"""
        start_time = time.time()
        
        try:
            self.state.update_status("busy", task.task_id)
            
            # 1. 任务分解
            subtasks = await self.execute_tool(
                "task_decomposition",
                task_description=task.description,
                input_data=task.input_data
            )
            
            # 2. 智能体选择
            agent_assignments = await self.execute_tool(
                "agent_selection",
                subtasks=subtasks
            )
            
            # 3. 协调执行
            execution_results = await self._coordinate_execution(
                subtasks, agent_assignments, task.task_id
            )
            
            # 4. 结果聚合
            final_result = await self.execute_tool(
                "result_aggregation",
                results=execution_results,
                original_task=task.description
            )
            
            execution_time = time.time() - start_time
            
            self.state.update_status("idle")
            
            return CAMELResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result_data={
                    'coordination_plan': {
                        'subtasks': subtasks,
                        'agent_assignments': agent_assignments
                    },
                    'execution_results': execution_results,
                    'final_result': final_result
                },
                execution_time=execution_time,
                quality_score=self._calculate_coordination_quality(execution_results)
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.state.update_status("error")
            
            return CAMELResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                result_data={},
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _decompose_task(self, task_description: str, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """任务分解"""
        prompt = f"""
请将以下任务分解为具体的子任务：

任务描述：{task_description}
输入数据：{json.dumps(input_data, ensure_ascii=False, indent=2)}

请返回JSON格式的子任务列表，每个子任务包含：
- task_type: 任务类型（search/extract/analyze/generate/review）
- description: 子任务描述
- priority: 优先级（1-5）
- dependencies: 依赖的其他子任务ID
- estimated_time: 预估执行时间（秒）
"""
        
        response = await self.communicate_with_llm(prompt)
        
        try:
            subtasks = json.loads(response)
            return subtasks if isinstance(subtasks, list) else [subtasks]
        except json.JSONDecodeError:
            # 如果LLM返回的不是有效JSON，创建默认分解
            return [
                {
                    "task_type": "analyze",
                    "description": f"分析任务：{task_description}",
                    "priority": 1,
                    "dependencies": [],
                    "estimated_time": 30
                }
            ]
    
    async def _select_agents(self, subtasks: List[Dict[str, Any]]) -> Dict[str, str]:
        """智能体选择"""
        available_agents = self.config.get('available_agents', {})
        assignments = {}
        
        for i, subtask in enumerate(subtasks):
            task_type = subtask.get('task_type', 'analyze')
            
            # 根据任务类型选择合适的智能体
            if task_type == 'search':
                assignments[f"subtask_{i}"] = available_agents.get('searcher', 'searcher_001')
            elif task_type == 'extract':
                assignments[f"subtask_{i}"] = available_agents.get('extractor', 'extractor_001')
            elif task_type == 'analyze':
                assignments[f"subtask_{i}"] = available_agents.get('analyzer', 'analyzer_001')
            elif task_type == 'generate':
                assignments[f"subtask_{i}"] = available_agents.get('generator', 'generator_001')
            elif task_type == 'review':
                assignments[f"subtask_{i}"] = available_agents.get('reviewer', 'reviewer_001')
            else:
                assignments[f"subtask_{i}"] = available_agents.get('analyzer', 'analyzer_001')
        
        return assignments
    
    async def _coordinate_execution(self, subtasks: List[Dict[str, Any]], 
                                  assignments: Dict[str, str], 
                                  parent_task_id: str) -> List[Dict[str, Any]]:
        """协调执行子任务"""
        results = []
        
        # 简化实现：串行执行所有子任务
        for i, subtask in enumerate(subtasks):
            subtask_id = f"subtask_{i}"
            assigned_agent = assignments.get(subtask_id)
            
            if assigned_agent:
                # 发送任务请求给指定智能体
                await self.send_message(
                    receiver_id=assigned_agent,
                    message_type=MessageType.TASK_REQUEST,
                    content={
                        'subtask': subtask,
                        'parent_task_id': parent_task_id
                    },
                    task_id=parent_task_id
                )
                
                # 模拟等待结果（实际实现中应该通过消息机制）
                await asyncio.sleep(subtask.get('estimated_time', 30) / 10)  # 加速模拟
                
                # 模拟结果
                result = {
                    'subtask_id': subtask_id,
                    'agent_id': assigned_agent,
                    'success': True,
                    'result': f"完成子任务：{subtask['description']}",
                    'execution_time': subtask.get('estimated_time', 30)
                }
                results.append(result)
        
        return results
    
    async def _aggregate_results(self, results: List[Dict[str, Any]], 
                               original_task: str) -> Dict[str, Any]:
        """聚合结果"""
        prompt = f"""
请基于以下子任务执行结果，生成对原始任务的综合回答：

原始任务：{original_task}

子任务结果：
{json.dumps(results, ensure_ascii=False, indent=2)}

请返回JSON格式的聚合结果，包含：
- summary: 综合总结
- key_findings: 关键发现
- recommendations: 建议
- confidence: 置信度（0-1）
"""
        
        response = await self.communicate_with_llm(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'summary': f"已完成任务：{original_task}",
                'key_findings': [f"执行了{len(results)}个子任务"],
                'recommendations': ["任务执行成功"],
                'confidence': 0.8
            }
    
    def _calculate_coordination_quality(self, results: List[Dict[str, Any]]) -> float:
        """计算协调质量分数"""
        if not results:
            return 0.0
        
        success_rate = sum(1 for r in results if r.get('success', False)) / len(results)
        return success_rate


class SearcherAgent(BaseCAMELAgent):
    """搜索代理
    
    负责多源信息搜索和网站发现
    基于CAMEL框架的搜索者角色
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentRole.SEARCHER, config)
    
    def _generate_system_prompt(self) -> str:
        """生成搜索代理的系统提示"""
        return """
你是一个专业的搜索代理，负责从多个数据源获取相关信息。

你的职责包括：
1. 理解搜索需求和关键词
2. 选择合适的搜索引擎和数据源
3. 执行高效的搜索策略
4. 过滤和排序搜索结果
5. 发现相关的网站和资源

搜索策略：
- 使用多样化的关键词组合
- 利用不同的搜索引擎特点
- 考虑时效性和权威性
- 避免重复和低质量内容

请始终返回结构化的搜索结果。
"""
    
    def _register_tools(self) -> None:
        """注册搜索代理工具"""
        self.register_tool(AgentTool(
            name="web_search",
            description="执行网络搜索",
            function=self._web_search
        ))
        
        self.register_tool(AgentTool(
            name="document_search",
            description="搜索文档库",
            function=self._document_search
        ))
        
        self.register_tool(AgentTool(
            name="result_ranking",
            description="对搜索结果进行排序",
            function=self._rank_results
        ))
    
    def validate_config(self) -> bool:
        """验证配置"""
        required_keys = ['search_engines', 'max_results']
        return all(key in self.config for key in required_keys)
    
    async def process_task(self, task: CAMELTask) -> CAMELResult:
        """处理搜索任务"""
        start_time = time.time()
        
        try:
            self.state.update_status("busy", task.task_id)
            
            query = task.input_data.get('query', task.description)
            search_type = task.input_data.get('search_type', 'web')
            max_results = task.input_data.get('max_results', self.config.get('max_results', 10))
            
            # 执行搜索
            if search_type == 'web':
                search_results = await self.execute_tool(
                    "web_search",
                    query=query,
                    max_results=max_results
                )
            else:
                search_results = await self.execute_tool(
                    "document_search",
                    query=query,
                    max_results=max_results
                )
            
            # 结果排序
            ranked_results = await self.execute_tool(
                "result_ranking",
                results=search_results,
                query=query
            )
            
            execution_time = time.time() - start_time
            
            self.state.update_status("idle")
            
            return CAMELResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result_data={
                    'search_query': query,
                    'search_type': search_type,
                    'results': ranked_results,
                    'total_found': len(ranked_results)
                },
                execution_time=execution_time,
                quality_score=self._calculate_search_quality(ranked_results)
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.state.update_status("error")
            
            return CAMELResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                result_data={},
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _web_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """执行网络搜索"""
        # 模拟网络搜索
        await asyncio.sleep(1.0)  # 模拟搜索延迟
        
        results = []
        search_engines = self.config.get('search_engines', ['google', 'bing'])
        
        for engine in search_engines:
            for i in range(max_results // len(search_engines)):
                result = {
                    'title': f"{engine}搜索结果 {i+1}: {query}",
                    'url': f"https://{engine}.example.com/result/{i+1}",
                    'snippet': f"这是来自{engine}的搜索结果摘要，包含关键词：{query}",
                    'source': engine,
                    'relevance_score': 0.9 - (i * 0.1),
                    'timestamp': datetime.now().isoformat()
                }
                results.append(result)
        
        return results
    
    async def _document_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """搜索文档库"""
        # 模拟文档搜索
        await asyncio.sleep(0.5)
        
        results = []
        for i in range(max_results):
            result = {
                'title': f"文档 {i+1}: {query}",
                'content': f"这是文档内容摘要，包含关键词：{query}",
                'document_type': 'pdf',
                'relevance_score': 0.95 - (i * 0.05),
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
        
        return results
    
    async def _rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """对搜索结果进行排序"""
        # 按相关性分数排序
        return sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def _calculate_search_quality(self, results: List[Dict[str, Any]]) -> float:
        """计算搜索质量分数"""
        if not results:
            return 0.0
        
        avg_relevance = sum(r.get('relevance_score', 0) for r in results) / len(results)
        return avg_relevance


class ExtractorAgent(BaseCAMELAgent):
    """提取代理
    
    负责从网页和文档中提取结构化信息
    基于CAMEL框架的提取者角色
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentRole.EXTRACTOR, config)
    
    def _generate_system_prompt(self) -> str:
        """生成提取代理的系统提示"""
        return """
你是一个专业的信息提取代理，负责从各种数据源中提取结构化信息。

你的职责包括：
1. 解析网页和文档内容
2. 识别和提取关键信息
3. 清理和标准化数据
4. 构建结构化的数据格式
5. 处理多模态内容（文本、图像、表格）

提取原则：
- 保持信息的准确性和完整性
- 去除噪声和无关内容
- 标准化数据格式
- 保留重要的上下文信息

请始终返回结构化的提取结果。
"""
    
    def _register_tools(self) -> None:
        """注册提取代理工具"""
        self.register_tool(AgentTool(
            name="content_extraction",
            description="提取内容",
            function=self._extract_content
        ))
        
        self.register_tool(AgentTool(
            name="data_cleaning",
            description="清理数据",
            function=self._clean_data
        ))
        
        self.register_tool(AgentTool(
            name="structure_data",
            description="结构化数据",
            function=self._structure_data
        ))
    
    def validate_config(self) -> bool:
        """验证配置"""
        required_keys = ['extraction_rules']
        return all(key in self.config for key in required_keys)
    
    async def process_task(self, task: CAMELTask) -> CAMELResult:
        """处理提取任务"""
        start_time = time.time()
        
        try:
            self.state.update_status("busy", task.task_id)
            
            sources = task.input_data.get('sources', [])
            extraction_type = task.input_data.get('extraction_type', 'text')
            
            extracted_data = []
            
            for source in sources:
                # 提取内容
                content = await self.execute_tool(
                    "content_extraction",
                    source=source,
                    extraction_type=extraction_type
                )
                
                # 清理数据
                cleaned_content = await self.execute_tool(
                    "data_cleaning",
                    content=content
                )
                
                # 结构化数据
                structured_data = await self.execute_tool(
                    "structure_data",
                    content=cleaned_content,
                    source=source
                )
                
                extracted_data.append(structured_data)
            
            execution_time = time.time() - start_time
            
            self.state.update_status("idle")
            
            return CAMELResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result_data={
                    'extraction_type': extraction_type,
                    'sources_processed': len(sources),
                    'extracted_data': extracted_data
                },
                execution_time=execution_time,
                quality_score=self._calculate_extraction_quality(extracted_data)
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.state.update_status("error")
            
            return CAMELResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                result_data={},
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _extract_content(self, source: Dict[str, Any], extraction_type: str) -> Dict[str, Any]:
        """提取内容"""
        # 模拟内容提取
        await asyncio.sleep(0.8)
        
        if extraction_type == 'text':
            return {
                'text': f"从{source.get('url', '未知来源')}提取的文本内容",
                'word_count': 500,
                'language': 'zh-CN'
            }
        elif extraction_type == 'data':
            return {
                'tables': [{'headers': ['列1', '列2'], 'rows': [['数据1', '数据2']]}],
                'lists': [['项目1', '项目2', '项目3']],
                'metadata': {'extraction_date': datetime.now().isoformat()}
            }
        else:
            return {
                'content': f"从{source.get('url', '未知来源')}提取的内容",
                'type': extraction_type
            }
    
    async def _clean_data(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """清理数据"""
        # 模拟数据清理
        await asyncio.sleep(0.3)
        
        # 简单的清理逻辑
        cleaned_content = content.copy()
        
        if 'text' in cleaned_content:
            # 模拟文本清理
            cleaned_content['text'] = cleaned_content['text'].strip()
            cleaned_content['cleaned'] = True
        
        return cleaned_content
    
    async def _structure_data(self, content: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """结构化数据"""
        # 模拟数据结构化
        await asyncio.sleep(0.2)
        
        return {
            'source_url': source.get('url', ''),
            'source_title': source.get('title', ''),
            'extracted_content': content,
            'extraction_timestamp': datetime.now().isoformat(),
            'quality_indicators': {
                'completeness': 0.9,
                'accuracy': 0.85,
                'relevance': 0.8
            }
        }
    
    def _calculate_extraction_quality(self, extracted_data: List[Dict[str, Any]]) -> float:
        """计算提取质量分数"""
        if not extracted_data:
            return 0.0
        
        total_quality = 0.0
        for data in extracted_data:
            quality_indicators = data.get('quality_indicators', {})
            avg_quality = sum(quality_indicators.values()) / len(quality_indicators) if quality_indicators else 0.5
            total_quality += avg_quality
        
        return total_quality / len(extracted_data)


class AnalyzerAgent(BaseCAMELAgent):
    """分析代理
    
    负责数据分析和洞察生成
    基于CAMEL框架的分析者角色
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentRole.ANALYZER, config)
    
    def _generate_system_prompt(self) -> str:
        """生成分析代理的系统提示"""
        return """
你是一个专业的数据分析代理，负责深度分析和洞察生成。

你的职责包括：
1. 分析结构化和非结构化数据
2. 识别模式、趋势和异常
3. 生成数据洞察和建议
4. 进行统计分析和可视化
5. 提供决策支持信息

分析原则：
- 基于数据的客观分析
- 多角度和多层次分析
- 关注实用性和可操作性
- 提供可信度评估

请始终返回结构化的分析结果。
"""
    
    def _register_tools(self) -> None:
        """注册分析代理工具"""
        self.register_tool(AgentTool(
            name="statistical_analysis",
            description="统计分析",
            function=self._statistical_analysis
        ))
        
        self.register_tool(AgentTool(
            name="pattern_recognition",
            description="模式识别",
            function=self._pattern_recognition
        ))
        
        self.register_tool(AgentTool(
            name="insight_generation",
            description="洞察生成",
            function=self._generate_insights
        ))
    
    def validate_config(self) -> bool:
        """验证配置"""
        required_keys = ['analysis_methods']
        return all(key in self.config for key in required_keys)
    
    async def process_task(self, task: CAMELTask) -> CAMELResult:
        """处理分析任务"""
        start_time = time.time()
        
        try:
            self.state.update_status("busy", task.task_id)
            
            data = task.input_data.get('data', [])
            analysis_type = task.input_data.get('analysis_type', 'comprehensive')
            
            # 统计分析
            stats = await self.execute_tool(
                "statistical_analysis",
                data=data,
                analysis_type=analysis_type
            )
            
            # 模式识别
            patterns = await self.execute_tool(
                "pattern_recognition",
                data=data
            )
            
            # 洞察生成
            insights = await self.execute_tool(
                "insight_generation",
                stats=stats,
                patterns=patterns,
                context=task.description
            )
            
            execution_time = time.time() - start_time
            
            self.state.update_status("idle")
            
            return CAMELResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result_data={
                    'analysis_type': analysis_type,
                    'statistical_analysis': stats,
                    'patterns': patterns,
                    'insights': insights,
                    'data_summary': {
                        'total_records': len(data),
                        'analysis_methods': self.config.get('analysis_methods', [])
                    }
                },
                execution_time=execution_time,
                quality_score=self._calculate_analysis_quality(insights)
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.state.update_status("error")
            
            return CAMELResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                result_data={},
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _statistical_analysis(self, data: List[Any], analysis_type: str) -> Dict[str, Any]:
        """统计分析"""
        # 模拟统计分析
        await asyncio.sleep(1.2)
        
        return {
            'descriptive_stats': {
                'count': len(data),
                'mean': 75.5,
                'median': 78.0,
                'std_dev': 12.3
            },
            'distribution': {
                'normal': True,
                'skewness': 0.15,
                'kurtosis': -0.8
            },
            'confidence_intervals': {
                'mean_95_ci': [72.1, 78.9],
                'median_95_ci': [74.2, 81.8]
            }
        }
    
    async def _pattern_recognition(self, data: List[Any]) -> List[Dict[str, Any]]:
        """模式识别"""
        # 模拟模式识别
        await asyncio.sleep(0.8)
        
        return [
            {
                'pattern_type': 'trend',
                'description': '数据呈现上升趋势',
                'confidence': 0.85,
                'significance': 'high'
            },
            {
                'pattern_type': 'seasonality',
                'description': '存在周期性模式',
                'confidence': 0.72,
                'significance': 'medium'
            }
        ]
    
    async def _generate_insights(self, stats: Dict[str, Any], 
                               patterns: List[Dict[str, Any]], 
                               context: str) -> Dict[str, Any]:
        """生成洞察"""
        prompt = f"""
基于以下统计分析和模式识别结果，生成数据洞察：

上下文：{context}

统计分析：
{json.dumps(stats, ensure_ascii=False, indent=2)}

识别的模式：
{json.dumps(patterns, ensure_ascii=False, indent=2)}

请返回JSON格式的洞察，包含：
- key_findings: 关键发现
- implications: 影响和意义
- recommendations: 建议
- risk_factors: 风险因素
- confidence_level: 置信度
"""
        
        response = await self.communicate_with_llm(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'key_findings': ['数据分析完成'],
                'implications': ['需要进一步分析'],
                'recommendations': ['继续监控数据变化'],
                'risk_factors': ['数据质量需要验证'],
                'confidence_level': 0.7
            }
    
    def _calculate_analysis_quality(self, insights: Dict[str, Any]) -> float:
        """计算分析质量分数"""
        confidence_level = insights.get('confidence_level', 0.5)
        completeness = 1.0 if all(key in insights for key in ['key_findings', 'implications', 'recommendations']) else 0.5
        
        return (confidence_level + completeness) / 2