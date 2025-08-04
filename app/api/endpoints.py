"""FastAPI endpoints for the AI Assistant System."""

import time
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile
import os

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.api.models import *
from app.agents.assistant import AssistantAgent
from app.agents.code_agent import CodeAgent
from app.agents.docs_agent import DocsAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.tool_agent import ToolAgent
from app.core.document_processor import document_processor
from app.core.memory import memory
from app.core.llm import llm_manager


# Initialize FastAPI app
app = FastAPI(
    title="AI Assistant System",
    description="A modular, intelligent backend platform with multi-agent architecture",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
assistant_agent = AssistantAgent()
code_agent = CodeAgent()
docs_agent = DocsAgent()
planner_agent = PlannerAgent()
tool_agent = ToolAgent()

# Register specialized agents with the assistant
assistant_agent.register_agent(code_agent)
assistant_agent.register_agent(docs_agent)
assistant_agent.register_agent(planner_agent)
assistant_agent.register_agent(tool_agent)

# Global state
active_conversations = {}
generated_projects = {}


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    logger.info("Starting AI Assistant System...")
    logger.info(f"Server running on {settings.host}:{settings.port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AI Assistant System...")
    await llm_manager.close()


# Health and status endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        dependencies={
            "openrouter": "connected",
            "vector_memory": "active",
            "document_processor": "ready"
        }
    )


@app.get("/status", response_model=SystemStatusResponse)
async def system_status():
    """Get system status and statistics."""
    start_time = time.time()
    
    # Get agent statuses
    agents_status = {
        "assistant": assistant_agent.get_status(),
        "code": code_agent.get_status(),
        "docs": docs_agent.get_status(),
        "planner": planner_agent.get_status(),
        "tool": tool_agent.get_status()
    }
    
    # Get memory statistics
    memory_stats = memory.get_stats()
    
    return SystemStatusResponse(
        status="operational",
        agents=agents_status,
        memory_stats=memory_stats,
        active_conversations=len(active_conversations),
        total_documents=0,  # Would query database
        uptime=time.time() - start_time
    )


# Chat endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests."""
    start_time = time.time()
    
    try:
        # Handle conversation context
        conversation_id = request.conversation_id or int(time.time())
        
        # Process the chat message
        response = await assistant_agent.chat(
            message=request.message,
            context={
                "conversation_id": conversation_id,
                "model_type": request.model_type,
                **request.context
            }
        )
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            model_used="auto-selected",  # Would track actual model used
            agent_used="AssistantAgent",
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Handle streaming chat requests."""
    try:
        async def generate_stream():
            conversation_id = request.conversation_id or int(time.time())
            
            async for chunk in assistant_agent.chat_stream(
                message=request.message,
                context={
                    "conversation_id": conversation_id,
                    **request.context
                }
            ):
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"Streaming chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Document endpoints
@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: Optional[int] = None
):
    """Upload and process a document."""
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in document_processor.get_supported_formats():
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {file_extension}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Process document
            result = await document_processor.process_document(
                file_path=temp_file_path,
                file_content=file_content,
                original_filename=file.filename,
                conversation_id=conversation_id
            )
            
            processing_time = time.time() - start_time
            
            if result.get('processed'):
                return DocumentUploadResponse(
                    document_id=result['content_hash'],
                    filename=file.filename,
                    file_size=len(file_content),
                    file_type=file.content_type or 'application/octet-stream',
                    processed=True,
                    chunks_created=len(result.get('chunks', [])),
                    processing_time=processing_time
                )
            else:
                return DocumentUploadResponse(
                    document_id="",
                    filename=file.filename,
                    file_size=len(file_content),
                    file_type=file.content_type or 'application/octet-stream',
                    processed=False,
                    chunks_created=0,
                    processing_time=processing_time,
                    error=result.get('error', 'Unknown processing error')
                )
                
        finally:
            # Cleanup temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/search", response_model=DocumentSearchResponse)
async def search_documents(request: DocumentSearchRequest):
    """Search for relevant document content."""
    start_time = time.time()
    
    try:
        results = await document_processor.search_documents(
            query=request.query,
            conversation_id=request.conversation_id,
            k=request.limit
        )
        
        processing_time = time.time() - start_time
        
        return DocumentSearchResponse(
            results=results,
            total_found=len(results),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent task endpoints
@app.post("/agents/task", response_model=AgentTaskResponse)
async def create_agent_task(request: AgentTaskRequest):
    """Create and execute a task with a specific agent."""
    start_time = time.time()
    
    try:
        # Get the requested agent
        agent_map = {
            "CodeAgent": code_agent,
            "DocsAgent": docs_agent,
            "PlannerAgent": planner_agent,
            "ToolAgent": tool_agent,
            "AssistantAgent": assistant_agent
        }
        
        if request.agent_name not in agent_map:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {request.agent_name}")
        
        agent = agent_map[request.agent_name]
        
        # Create and execute task
        task_id = await agent.add_task(
            description=request.task_description,
            context=request.context
        )
        
        task_result = await agent.execute_task(task_id)
        processing_time = time.time() - start_time
        
        return AgentTaskResponse(
            task_id=task_result.id,
            agent_name=request.agent_name,
            status=task_result.status.value,
            result=task_result.result,
            error=task_result.error,
            processing_time=processing_time,
            created_at=task_result.created_at,
            completed_at=task_result.completed_at
        )
        
    except Exception as e:
        logger.error(f"Agent task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_name}/status")
async def get_agent_status(agent_name: str):
    """Get status of a specific agent."""
    agent_map = {
        "code": code_agent,
        "docs": docs_agent,
        "planner": planner_agent,
        "tool": tool_agent,
        "assistant": assistant_agent
    }
    
    if agent_name.lower() not in agent_map:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_name}")
    
    agent = agent_map[agent_name.lower()]
    return agent.get_status()


# Project generation endpoints
@app.post("/projects/generate", response_model=ProjectGenerationResponse)
async def generate_project(request: ProjectGenerationRequest, background_tasks: BackgroundTasks):
    """Generate a complete project based on requirements."""
    start_time = time.time()
    
    try:
        from app.core.project_generator import project_generator
        
        # Generate project using the dedicated project generator
        project_info = await project_generator.generate_project(
            project_type=request.project_type,
            name=request.name,
            description=request.description,
            requirements=request.requirements,
            technologies=request.technologies,
            additional_context=request.additional_context
        )
        
        processing_time = time.time() - start_time
        
        if project_info.get("status") == "completed":
            # Store project info
            generated_projects[project_info["project_id"]] = project_info
            
            return ProjectGenerationResponse(
                project_id=project_info["project_id"],
                status="completed",
                files_created=project_info["files_created"],
                project_path=project_info["path"],
                download_url=f"/projects/{project_info['project_id']}/download",
                processing_time=processing_time
            )
        else:
            return ProjectGenerationResponse(
                project_id=project_info.get("project_id", "unknown"),
                status="failed",
                files_created=0,
                project_path="",
                processing_time=processing_time,
                error=project_info.get("error", "Unknown error")
            )
            
    except Exception as e:
        logger.error(f"Project generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get project information."""
    if project_id not in generated_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return generated_projects[project_id]


@app.get("/projects/{project_id}/download")
async def download_project(project_id: str):
    """Download project as a zip file."""
    if project_id not in generated_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_info = generated_projects[project_id]
    zip_path = project_info.get("zip_path")
    
    if not zip_path or not Path(zip_path).exists():
        raise HTTPException(status_code=404, detail="Project file not found")
    
    return FileResponse(
        path=zip_path,
        filename=f"{project_info['name']}.zip",
        media_type="application/zip"
    )


# Memory endpoints
@app.post("/memory/search", response_model=MemorySearchResponse)
async def search_memory(request: MemorySearchRequest):
    """Search the vector memory system."""
    start_time = time.time()
    
    try:
        results = memory.search_memories(
            query=request.query,
            k=request.limit,
            threshold=request.threshold
        )
        
        processing_time = time.time() - start_time
        
        return MemorySearchResponse(
            results=results,
            total_found=len(results),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/stats")
async def get_memory_stats():
    """Get memory system statistics."""
    return memory.get_stats()


# Conversation management endpoints
@app.get("/conversations")
async def list_conversations():
    """List all conversations."""
    # This would query the database for conversations
    # For now, return active conversations
    return [
        {
            "id": conv_id,
            "title": f"Conversation {conv_id}",
            "created_at": time.time(),
            "message_count": 0,
            "is_active": True
        }
        for conv_id in active_conversations.keys()
    ]


@app.post("/conversations")
async def create_conversation():
    """Create a new conversation."""
    conversation_id = int(time.time())
    active_conversations[conversation_id] = {
        "created_at": time.time(),
        "messages": []
    }
    
    return {"conversation_id": conversation_id}


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int):
    """Get conversation details."""
    if conversation_id not in active_conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return active_conversations[conversation_id]


# Tool and utility endpoints
@app.post("/tools/execute")
async def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Execute a tool or system command."""
    try:
        task_description = f"Execute tool: {tool_name} with parameters: {parameters}"
        
        task_id = await tool_agent.add_task(
            description=task_description,
            context={
                "tool_name": tool_name,
                "parameters": parameters
            }
        )
        
        task_result = await tool_agent.execute_task(task_id)
        
        return {
            "task_id": task_result.id,
            "status": task_result.status.value,
            "result": task_result.result,
            "error": task_result.error
        }
        
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return ErrorResponse(
        error=exc.detail,
        error_code=str(exc.status_code),
        details={"status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return ErrorResponse(
        error="Internal server error",
        error_code="500",
        details={"exception": str(exc)}
    )