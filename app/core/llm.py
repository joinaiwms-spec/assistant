"""LLM integration with OpenRouter for multiple model support."""

import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from enum import Enum

import httpx
from loguru import logger
from pydantic import BaseModel

from app.config import settings


class ModelType(str, Enum):
    """Available model types."""
    DEFAULT = "default"
    MISTRAL = "mistral"
    QWEN = "qwen"


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str
    content: str
    name: Optional[str] = None


class LLMResponse(BaseModel):
    """LLM response model."""
    content: str
    model: str
    usage: Dict[str, Any]
    finish_reason: str


class OpenRouterClient:
    """OpenRouter API client for multiple LLM models."""
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.models = {
            ModelType.DEFAULT: settings.default_model,
            ModelType.MISTRAL: settings.mistral_model,
            ModelType.QWEN: settings.qwen_model,
        }
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "AI Assistant System",
                "Content-Type": "application/json"
            }
        )
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_type: ModelType = ModelType.DEFAULT,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion."""
        try:
            model = self.models[model_type]
            
            payload = {
                "model": model,
                "messages": [msg.dict(exclude_none=True) for msg in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
                **kwargs
            }
            
            logger.debug(f"Sending request to {model} with {len(messages)} messages")
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                raise ValueError("No choices in response")
            
            choice = data["choices"][0]
            
            return LLMResponse(
                content=choice["message"]["content"],
                model=data.get("model", model),
                usage=data.get("usage", {}),
                finish_reason=choice.get("finish_reason", "unknown")
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from OpenRouter: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        model_type: ModelType = ModelType.DEFAULT,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion."""
        try:
            model = self.models[model_type]
            
            payload = {
                "model": model,
                "messages": [msg.dict(exclude_none=True) for msg in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
                **kwargs
            }
            
            logger.debug(f"Starting stream with {model}")
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            import json
                            data = json.loads(data_str)
                            
                            if "choices" in data and data["choices"]:
                                choice = data["choices"][0]
                                if "delta" in choice and "content" in choice["delta"]:
                                    content = choice["delta"]["content"]
                                    if content:
                                        yield content
                        except json.JSONDecodeError:
                            continue
                        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in streaming: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error in streaming completion: {e}")
            raise
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Get list of available models from OpenRouter."""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return {"data": []}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class LLMManager:
    """Manager for LLM operations with different models."""
    
    def __init__(self):
        self.client = OpenRouterClient()
        self._model_capabilities = {
            ModelType.DEFAULT: {"good_for": ["general", "chat", "reasoning"]},
            ModelType.MISTRAL: {"good_for": ["code", "technical", "analysis"]},
            ModelType.QWEN: {"good_for": ["multilingual", "creative", "writing"]},
        }
    
    def select_best_model(self, task_type: str, context: str = "") -> ModelType:
        """Select the best model for a given task type."""
        # Simple heuristic-based model selection
        task_lower = task_type.lower()
        
        if any(keyword in task_lower for keyword in ["code", "programming", "debug", "technical"]):
            return ModelType.MISTRAL
        elif any(keyword in task_lower for keyword in ["creative", "write", "story", "translate"]):
            return ModelType.QWEN
        else:
            return ModelType.DEFAULT
    
    async def generate_response(
        self,
        messages: List[ChatMessage],
        model_type: Optional[ModelType] = None,
        task_type: str = "general",
        **kwargs
    ) -> LLMResponse:
        """Generate a response using the appropriate model."""
        if model_type is None:
            model_type = self.select_best_model(task_type)
        
        return await self.client.chat_completion(
            messages=messages,
            model_type=model_type,
            **kwargs
        )
    
    async def generate_response_stream(
        self,
        messages: List[ChatMessage],
        model_type: Optional[ModelType] = None,
        task_type: str = "general",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response using the appropriate model."""
        if model_type is None:
            model_type = self.select_best_model(task_type)
        
        async for chunk in self.client.chat_completion_stream(
            messages=messages,
            model_type=model_type,
            **kwargs
        ):
            yield chunk
    
    def get_model_info(self, model_type: ModelType) -> Dict[str, Any]:
        """Get information about a specific model."""
        return {
            "name": self.client.models[model_type],
            "type": model_type.value,
            "capabilities": self._model_capabilities.get(model_type, {})
        }
    
    async def close(self):
        """Close the LLM manager."""
        await self.client.close()


# Global LLM manager instance
llm_manager = LLMManager()