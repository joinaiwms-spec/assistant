"""Pydantic models for API requests and responses."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.llm import ModelType


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="The user's message")
    conversation_id: Optional[int] = Field(None, description="Conversation ID for context")
    model_type: Optional[ModelType] = Field(None, description="Preferred model type")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    stream: bool = Field(False, description="Whether to stream the response")
    images: Optional[List[str]] = Field(None, description="List of image URLs for vision tasks")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="Assistant's response")
    conversation_id: int = Field(..., description="Conversation ID")
    model_used: str = Field(..., description="Model that generated the response")
    agent_used: Optional[str] = Field(None, description="Agent that handled the request")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    processing_time: float = Field(..., description="Processing time in seconds")


class DocumentUploadResponse(BaseModel):
    """Document upload response model."""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="MIME type")
    processed: bool = Field(..., description="Whether processing was successful")
    chunks_created: int = Field(..., description="Number of chunks created")
    processing_time: float = Field(..., description="Processing time in seconds")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class DocumentSearchRequest(BaseModel):
    """Document search request model."""
    query: str = Field(..., description="Search query")
    conversation_id: Optional[int] = Field(None, description="Limit search to conversation")
    limit: int = Field(5, description="Maximum number of results", ge=1, le=20)


class DocumentSearchResponse(BaseModel):
    """Document search response model."""
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total number of results found")
    processing_time: float = Field(..., description="Search time in seconds")


class AgentTaskRequest(BaseModel):
    """Agent task request model."""
    agent_name: str = Field(..., description="Name of the agent to use")
    task_description: str = Field(..., description="Description of the task")
    context: Dict[str, Any] = Field(default_factory=dict, description="Task context")
    priority: int = Field(1, description="Task priority (1-5)", ge=1, le=5)


class AgentTaskResponse(BaseModel):
    """Agent task response model."""
    task_id: str = Field(..., description="Unique task identifier")
    agent_name: str = Field(..., description="Agent that handled the task")
    status: str = Field(..., description="Task status")
    result: Optional[str] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if task failed")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    created_at: datetime = Field(..., description="Task creation time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")


class ProjectGenerationRequest(BaseModel):
    """Project generation request model."""
    project_type: str = Field(..., description="Type of project to generate")
    requirements: List[str] = Field(..., description="Project requirements")
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    technologies: List[str] = Field(default_factory=list, description="Preferred technologies")
    additional_context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ProjectGenerationResponse(BaseModel):
    """Project generation response model."""
    project_id: str = Field(..., description="Unique project identifier")
    status: str = Field(..., description="Generation status")
    files_created: int = Field(..., description="Number of files created")
    project_path: str = Field(..., description="Path to generated project")
    download_url: Optional[str] = Field(None, description="Download URL for project archive")
    processing_time: float = Field(..., description="Generation time in seconds")
    error: Optional[str] = Field(None, description="Error message if generation failed")


class SystemStatusResponse(BaseModel):
    """System status response model."""
    status: str = Field(..., description="Overall system status")
    agents: Dict[str, Dict[str, Any]] = Field(..., description="Agent status information")
    memory_stats: Dict[str, Any] = Field(..., description="Memory system statistics")
    active_conversations: int = Field(..., description="Number of active conversations")
    total_documents: int = Field(..., description="Total number of processed documents")
    uptime: float = Field(..., description="System uptime in seconds")


class ConversationResponse(BaseModel):
    """Conversation response model."""
    id: int = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")
    message_count: int = Field(..., description="Number of messages")
    is_active: bool = Field(..., description="Whether conversation is active")


class MessageResponse(BaseModel):
    """Message response model."""
    id: int = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    agent_type: Optional[str] = Field(None, description="Agent that generated the message")
    model_used: Optional[str] = Field(None, description="Model used to generate the message")
    created_at: datetime = Field(..., description="Creation time")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    dependencies: Dict[str, str] = Field(..., description="Dependency status")


class MemorySearchRequest(BaseModel):
    """Memory search request model."""
    query: str = Field(..., description="Search query")
    limit: int = Field(5, description="Maximum number of results", ge=1, le=20)
    threshold: float = Field(0.7, description="Similarity threshold", ge=0.0, le=1.0)


class MemorySearchResponse(BaseModel):
    """Memory search response model."""
    results: List[Dict[str, Any]] = Field(..., description="Memory search results")
    total_found: int = Field(..., description="Total number of results found")
    processing_time: float = Field(..., description="Search time in seconds")