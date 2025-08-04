"""Assistant Agent - Main coordinator for the multi-agent system."""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from loguru import logger

from app.agents.base import BaseAgent, AgentTask, TaskStatus
from app.core.llm import ChatMessage, ModelType


class AssistantAgent(BaseAgent):
    """Main assistant agent that coordinates other agents."""
    
    def __init__(self):
        super().__init__(
            name="AssistantAgent",
            description="Main coordinator that breaks down complex tasks and routes them to specialized agents",
            model_type=ModelType.DEFAULT
        )
        self.sub_agents: Dict[str, BaseAgent] = {}
    
    def _get_system_prompt(self) -> str:
        return """You are the AssistantAgent, the main coordinator of a multi-agent AI system. Your role is to:

1. Analyze user requests and break them down into subtasks
2. Route subtasks to the most appropriate specialized agents
3. Coordinate between agents to ensure tasks are completed efficiently
4. Synthesize results from multiple agents into coherent responses
5. Manage the overall conversation flow and context

Available specialized agents:
- CodeAgent: Handles programming, debugging, code generation, and technical analysis
- DocsAgent: Processes documents, extracts information, and answers document-related questions
- PlannerAgent: Creates project plans, manages workflows, and breaks down complex projects
- ToolAgent: Executes system commands, file operations, and external tool integrations

When analyzing a request:
1. Identify the main task type and complexity
2. Determine if it needs to be broken down into subtasks
3. Assign subtasks to appropriate agents
4. Coordinate execution and collect results
5. Provide a unified response to the user

Always be helpful, accurate, and efficient in your coordination."""
    
    def register_agent(self, agent: BaseAgent):
        """Register a specialized agent."""
        self.sub_agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    async def _execute_task(self, task: AgentTask) -> str:
        """Execute a coordination task."""
        try:
            # Analyze the task and determine if it needs delegation
            analysis = await self._analyze_task(task)
            
            if analysis["needs_delegation"]:
                return await self._delegate_and_coordinate(task, analysis)
            else:
                return await self._handle_directly(task)
                
        except Exception as e:
            logger.error(f"Error executing task in AssistantAgent: {e}")
            raise
    
    async def _analyze_task(self, task: AgentTask) -> Dict[str, Any]:
        """Analyze a task to determine how to handle it."""
        analysis_prompt = f"""
        Analyze this task and determine how to handle it:
        
        Task: {task.description}
        Context: {json.dumps(task.context, indent=2)}
        
        Respond with a JSON object containing:
        {{
            "needs_delegation": boolean,
            "task_type": "code|docs|planning|tools|general",
            "complexity": "low|medium|high",
            "subtasks": [
                {{
                    "description": "subtask description",
                    "agent": "CodeAgent|DocsAgent|PlannerAgent|ToolAgent",
                    "priority": 1-5
                }}
            ],
            "reasoning": "explanation of the analysis"
        }}
        """
        
        messages = [ChatMessage(role="user", content=analysis_prompt)]
        response = await self.generate_response(messages)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
            else:
                # Fallback analysis
                return {
                    "needs_delegation": False,
                    "task_type": "general",
                    "complexity": "medium",
                    "subtasks": [],
                    "reasoning": "Could not parse analysis, handling directly"
                }
        except json.JSONDecodeError:
            logger.warning("Failed to parse task analysis JSON")
            return {
                "needs_delegation": False,
                "task_type": "general",
                "complexity": "medium",
                "subtasks": [],
                "reasoning": "JSON parsing failed, handling directly"
            }
    
    async def _delegate_and_coordinate(self, task: AgentTask, analysis: Dict[str, Any]) -> str:
        """Delegate subtasks to appropriate agents and coordinate results."""
        results = []
        subtasks = analysis.get("subtasks", [])
        
        logger.info(f"Delegating task to {len(subtasks)} subtasks")
        
        for subtask_info in subtasks:
            agent_name = subtask_info.get("agent")
            if agent_name not in self.sub_agents:
                logger.warning(f"Agent {agent_name} not available, skipping subtask")
                continue
            
            agent = self.sub_agents[agent_name]
            
            try:
                # Add subtask to the agent
                subtask_id = await agent.add_task(
                    description=subtask_info["description"],
                    context={
                        **task.context,
                        "parent_task": task.id,
                        "priority": subtask_info.get("priority", 1)
                    }
                )
                
                # Execute the subtask
                subtask_result = await agent.execute_task(subtask_id)
                
                if subtask_result.status == TaskStatus.COMPLETED:
                    results.append({
                        "agent": agent_name,
                        "subtask": subtask_info["description"],
                        "result": subtask_result.result
                    })
                else:
                    results.append({
                        "agent": agent_name,
                        "subtask": subtask_info["description"],
                        "error": subtask_result.error
                    })
                    
            except Exception as e:
                logger.error(f"Error executing subtask with {agent_name}: {e}")
                results.append({
                    "agent": agent_name,
                    "subtask": subtask_info["description"],
                    "error": str(e)
                })
        
        # Synthesize results
        return await self._synthesize_results(task, results)
    
    async def _synthesize_results(self, task: AgentTask, results: List[Dict[str, Any]]) -> str:
        """Synthesize results from multiple agents into a coherent response."""
        synthesis_prompt = f"""
        Synthesize the following results from specialized agents into a coherent response for the user:
        
        Original Task: {task.description}
        
        Agent Results:
        {json.dumps(results, indent=2)}
        
        Provide a comprehensive, well-structured response that:
        1. Addresses the original task completely
        2. Integrates insights from all agents
        3. Is clear and helpful to the user
        4. Highlights any issues or limitations
        """
        
        messages = [ChatMessage(role="user", content=synthesis_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _handle_directly(self, task: AgentTask) -> str:
        """Handle a task directly without delegation."""
        # Get relevant memories
        memories = await self.get_relevant_memories(task.description)
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant context from previous interactions:\n"
            for mem in memories[:3]:  # Use top 3 memories
                memory_context += f"- {mem['text'][:200]}...\n"
        
        direct_prompt = f"""
        Handle this task directly:
        
        Task: {task.description}
        Context: {json.dumps(task.context, indent=2)}
        {memory_context}
        
        Provide a helpful, accurate, and complete response.
        """
        
        messages = [ChatMessage(role="user", content=direct_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def chat(self, message: str, context: Dict[str, Any] = None) -> str:
        """Handle a chat message from the user."""
        task_id = await self.add_task(
            description=f"Chat: {message}",
            context=context or {}
        )
        
        result = await self.execute_task(task_id)
        
        if result.status == TaskStatus.COMPLETED:
            return result.result
        else:
            return f"I encountered an error: {result.error}"
    
    async def chat_stream(self, message: str, context: Dict[str, Any] = None):
        """Handle a streaming chat message from the user."""
        # For streaming, we handle directly without complex delegation
        memories = await self.get_relevant_memories(message)
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant context:\n"
            for mem in memories[:2]:
                memory_context += f"- {mem['text'][:150]}...\n"
        
        chat_prompt = f"""
        User message: {message}
        Context: {json.dumps(context or {}, indent=2)}
        {memory_context}
        
        Respond helpfully and naturally to the user's message.
        """
        
        messages = [ChatMessage(role="user", content=chat_prompt)]
        
        async for chunk in self.generate_response_stream(messages):
            yield chunk