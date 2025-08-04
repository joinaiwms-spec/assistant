"""Base agent class for the multi-agent system."""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from loguru import logger

from app.core.llm import ChatMessage, LLMResponse, ModelType, llm_manager
from app.core.memory import memory


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentTask(BaseModel):
    """Task model for agent execution."""
    id: str
    description: str
    context: Dict[str, Any] = {}
    priority: int = 1
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    completed_at: Optional[datetime] = None


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, description: str, model_type: ModelType = ModelType.DEFAULT):
        self.name = name
        self.description = description
        self.model_type = model_type
        self.tasks: Dict[str, AgentTask] = {}
        self.system_prompt = self._get_system_prompt()
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    @abstractmethod
    async def _execute_task(self, task: AgentTask) -> str:
        """Execute a specific task. Must be implemented by subclasses."""
        pass
    
    async def add_task(self, description: str, context: Dict[str, Any] = None) -> str:
        """Add a new task to the agent's queue."""
        task_id = f"{self.name}_{len(self.tasks)}_{int(datetime.utcnow().timestamp())}"
        
        task = AgentTask(
            id=task_id,
            description=description,
            context=context or {}
        )
        
        self.tasks[task_id] = task
        logger.info(f"Added task {task_id} to {self.name}")
        
        return task_id
    
    async def execute_task(self, task_id: str) -> AgentTask:
        """Execute a specific task by ID."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        if task.status != TaskStatus.PENDING:
            return task
        
        task.status = TaskStatus.RUNNING
        logger.info(f"Executing task {task_id} on {self.name}")
        
        try:
            result = await self._execute_task(task)
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            # Store successful results in memory
            await self._store_in_memory(task)
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            logger.error(f"Task {task_id} failed: {e}")
        
        return task
    
    async def _store_in_memory(self, task: AgentTask):
        """Store task results in long-term memory."""
        try:
            memory_text = f"Agent: {self.name}\nTask: {task.description}\nResult: {task.result}"
            memory_metadata = {
                "agent": self.name,
                "task_id": task.id,
                "task_type": "execution",
                "timestamp": task.completed_at.isoformat() if task.completed_at else None
            }
            
            memory.add_memory(memory_text, memory_metadata)
            logger.debug(f"Stored task {task.id} results in memory")
            
        except Exception as e:
            logger.warning(f"Failed to store task in memory: {e}")
    
    async def get_relevant_memories(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Get relevant memories for the current task."""
        try:
            memories = memory.search_memories(query, k=k, threshold=0.6)
            return memories
        except Exception as e:
            logger.warning(f"Failed to retrieve memories: {e}")
            return []
    
    async def generate_response(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        """Generate a response using the agent's preferred model."""
        # Add system prompt if not present
        if not messages or messages[0].role != "system":
            system_message = ChatMessage(role="system", content=self.system_prompt)
            messages = [system_message] + messages
        
        return await llm_manager.generate_response(
            messages=messages,
            model_type=self.model_type,
            **kwargs
        )
    
    async def generate_response_stream(self, messages: List[ChatMessage], **kwargs):
        """Generate a streaming response using the agent's preferred model."""
        # Add system prompt if not present
        if not messages or messages[0].role != "system":
            system_message = ChatMessage(role="system", content=self.system_prompt)
            messages = [system_message] + messages
        
        async for chunk in llm_manager.generate_response_stream(
            messages=messages,
            model_type=self.model_type,
            **kwargs
        ):
            yield chunk
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and task summary."""
        task_counts = {
            "pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
        }
        
        return {
            "name": self.name,
            "description": self.description,
            "model_type": self.model_type.value,
            "total_tasks": len(self.tasks),
            "task_counts": task_counts
        }