"""Code Agent - Specialized agent for programming and technical tasks."""

import os
import subprocess
import tempfile
from typing import Dict, List, Any
from pathlib import Path

from loguru import logger

from app.agents.base import BaseAgent, AgentTask
from app.core.llm import ChatMessage, ModelType


class CodeAgent(BaseAgent):
    """Agent specialized in code generation, debugging, and technical analysis."""
    
    def __init__(self):
        super().__init__(
            name="CodeAgent",
            description="Specialized agent for programming, debugging, code generation, and technical analysis",
            model_type=ModelType.MISTRAL  # Mistral is good for code
        )
    
    def _get_system_prompt(self) -> str:
        return """You are CodeAgent, a specialized AI agent focused on programming and technical tasks. Your expertise includes:

1. Code generation in multiple programming languages
2. Code debugging and error analysis
3. Code review and optimization suggestions
4. Architecture and design pattern recommendations
5. Technical documentation and explanations
6. Algorithm and data structure implementation
7. API integration and development
8. Testing and quality assurance

When handling code-related tasks:
- Write clean, well-documented, and efficient code
- Follow best practices and coding standards
- Provide explanations for complex logic
- Consider security and performance implications
- Suggest improvements and alternatives when appropriate
- Include error handling and edge cases
- Use appropriate design patterns

Always strive for code that is readable, maintainable, and follows industry standards."""
    
    async def _execute_task(self, task: AgentTask) -> str:
        """Execute a code-related task."""
        try:
            task_type = self._classify_task(task.description)
            
            if task_type == "code_generation":
                return await self._generate_code(task)
            elif task_type == "code_review":
                return await self._review_code(task)
            elif task_type == "debugging":
                return await self._debug_code(task)
            elif task_type == "explanation":
                return await self._explain_code(task)
            elif task_type == "optimization":
                return await self._optimize_code(task)
            else:
                return await self._handle_general_code_task(task)
                
        except Exception as e:
            logger.error(f"Error in CodeAgent task execution: {e}")
            raise
    
    def _classify_task(self, description: str) -> str:
        """Classify the type of code task."""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["generate", "create", "write", "implement"]):
            return "code_generation"
        elif any(keyword in description_lower for keyword in ["review", "check", "analyze"]):
            return "code_review"
        elif any(keyword in description_lower for keyword in ["debug", "fix", "error", "bug"]):
            return "debugging"
        elif any(keyword in description_lower for keyword in ["explain", "understand", "how does"]):
            return "explanation"
        elif any(keyword in description_lower for keyword in ["optimize", "improve", "performance"]):
            return "optimization"
        else:
            return "general"
    
    async def _generate_code(self, task: AgentTask) -> str:
        """Generate code based on requirements."""
        # Get relevant code examples from memory
        memories = await self.get_relevant_memories(task.description)
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant code examples from previous work:\n"
            for mem in memories[:2]:
                memory_context += f"```\n{mem['text'][:300]}...\n```\n"
        
        generation_prompt = f"""
        Generate code for the following requirements:
        
        Task: {task.description}
        Context: {task.context}
        {memory_context}
        
        Please provide:
        1. Clean, well-documented code
        2. Explanation of the approach
        3. Usage examples
        4. Any important considerations or limitations
        
        Format your response with proper code blocks and explanations.
        """
        
        messages = [ChatMessage(role="user", content=generation_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _review_code(self, task: AgentTask) -> str:
        """Review and analyze code."""
        code = task.context.get("code", "")
        
        review_prompt = f"""
        Review the following code and provide detailed feedback:
        
        Task: {task.description}
        
        Code to review:
        ```
        {code}
        ```
        
        Please analyze:
        1. Code quality and readability
        2. Potential bugs or issues
        3. Performance considerations
        4. Security concerns
        5. Best practice adherence
        6. Suggestions for improvement
        
        Provide specific, actionable feedback.
        """
        
        messages = [ChatMessage(role="user", content=review_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _debug_code(self, task: AgentTask) -> str:
        """Debug code and identify issues."""
        code = task.context.get("code", "")
        error = task.context.get("error", "")
        
        debug_prompt = f"""
        Debug the following code issue:
        
        Task: {task.description}
        
        Code:
        ```
        {code}
        ```
        
        Error/Issue:
        {error}
        
        Please provide:
        1. Root cause analysis
        2. Step-by-step debugging approach
        3. Fixed code with explanations
        4. Prevention strategies for similar issues
        """
        
        messages = [ChatMessage(role="user", content=debug_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _explain_code(self, task: AgentTask) -> str:
        """Explain how code works."""
        code = task.context.get("code", "")
        
        explanation_prompt = f"""
        Explain the following code in detail:
        
        Task: {task.description}
        
        Code:
        ```
        {code}
        ```
        
        Please provide:
        1. Overall purpose and functionality
        2. Step-by-step breakdown
        3. Key concepts and algorithms used
        4. Input/output behavior
        5. Any notable design decisions
        
        Make the explanation clear and educational.
        """
        
        messages = [ChatMessage(role="user", content=explanation_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _optimize_code(self, task: AgentTask) -> str:
        """Optimize code for performance or other criteria."""
        code = task.context.get("code", "")
        
        optimization_prompt = f"""
        Optimize the following code:
        
        Task: {task.description}
        
        Current code:
        ```
        {code}
        ```
        
        Please provide:
        1. Analysis of current performance characteristics
        2. Identified optimization opportunities
        3. Optimized code with improvements
        4. Performance comparison and expected gains
        5. Trade-offs and considerations
        """
        
        messages = [ChatMessage(role="user", content=optimization_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _handle_general_code_task(self, task: AgentTask) -> str:
        """Handle general code-related tasks."""
        memories = await self.get_relevant_memories(task.description)
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant context:\n"
            for mem in memories[:3]:
                memory_context += f"- {mem['text'][:200]}...\n"
        
        general_prompt = f"""
        Handle this code-related task:
        
        Task: {task.description}
        Context: {task.context}
        {memory_context}
        
        Provide a comprehensive technical response that addresses the task requirements.
        Include code examples, explanations, and best practices where appropriate.
        """
        
        messages = [ChatMessage(role="user", content=general_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code in a safe environment (basic implementation)."""
        try:
            if language.lower() == "python":
                return await self._execute_python_code(code)
            else:
                return {"error": f"Code execution not supported for {language}"}
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {"error": str(e)}
    
    async def _execute_python_code(self, code: str) -> Dict[str, Any]:
        """Execute Python code safely."""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute the code
            result = subprocess.run(
                ["python", temp_file],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            # Clean up
            os.unlink(temp_file)
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "Code execution timed out"}
        except Exception as e:
            return {"error": str(e)}