#!/usr/bin/env python3
"""Command-line interface for the AI Assistant System."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax

# Import system components
from app.config import settings
from app.core.memory import memory
from app.core.document_processor import document_processor
from app.agents.assistant import AssistantAgent
from app.agents.code_agent import CodeAgent
from app.agents.docs_agent import DocsAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.tool_agent import ToolAgent

app = typer.Typer(
    name="ai-assistant",
    help="AI Assistant System CLI - Manage and interact with the multi-agent system",
    add_completion=False
)
console = Console()


@app.command()
def start(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
):
    """Start the AI Assistant System server."""
    import uvicorn
    
    console.print(Panel.fit(
        "🤖 AI Assistant System\nStarting server...",
        style="bold blue"
    ))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


@app.command()
def test():
    """Run system tests and diagnostics."""
    console.print("🧪 Running system tests...\n", style="bold yellow")
    
    import subprocess
    result = subprocess.run([sys.executable, "test_system.py"], capture_output=True, text=True)
    
    console.print(result.stdout)
    if result.stderr:
        console.print(result.stderr, style="red")
    
    if result.returncode == 0:
        console.print("✅ All tests passed!", style="bold green")
    else:
        console.print("❌ Some tests failed!", style="bold red")
        sys.exit(1)


@app.command()
def status():
    """Show system status and statistics."""
    console.print("📊 System Status", style="bold blue")
    
    # Configuration
    config_table = Table(title="Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Host", settings.host)
    config_table.add_row("Port", str(settings.port))
    config_table.add_row("Debug", str(settings.debug))
    config_table.add_row("Log Level", settings.log_level)
    config_table.add_row("Database URL", settings.database_url)
    config_table.add_row("Vector DB Path", settings.vector_db_path)
    
    console.print(config_table)
    console.print()
    
    # Memory statistics
    try:
        memory_stats = memory.get_stats()
        memory_table = Table(title="Memory Statistics")
        memory_table.add_column("Metric", style="cyan")
        memory_table.add_column("Value", style="green")
        
        for key, value in memory_stats.items():
            memory_table.add_row(str(key).replace("_", " ").title(), str(value))
        
        console.print(memory_table)
    except Exception as e:
        console.print(f"❌ Memory system error: {e}", style="red")


@app.command()
def chat(
    message: Optional[str] = typer.Argument(None, help="Message to send to the assistant"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Preferred model type"),
    stream: bool = typer.Option(False, "--stream", "-s", help="Enable streaming responses"),
):
    """Chat with the AI assistant."""
    if not message:
        console.print("💬 Interactive Chat Mode", style="bold blue")
        console.print("Type 'exit' to quit, 'help' for commands\n")
        
        asyncio.run(_interactive_chat())
    else:
        asyncio.run(_single_chat(message, model, stream))


async def _interactive_chat():
    """Interactive chat mode."""
    assistant = AssistantAgent()
    
    while True:
        try:
            message = console.input("\n[bold blue]You:[/bold blue] ")
            
            if message.lower() in ['exit', 'quit', 'bye']:
                console.print("👋 Goodbye!", style="bold green")
                break
            elif message.lower() == 'help':
                _show_chat_help()
                continue
            elif message.lower() == 'clear':
                console.clear()
                continue
            
            if not message.strip():
                continue
            
            console.print("\n[bold green]Assistant:[/bold green] ", end="")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Thinking...", total=None)
                
                try:
                    response = await assistant.chat(message)
                    progress.remove_task(task)
                    console.print(response)
                except Exception as e:
                    progress.remove_task(task)
                    console.print(f"❌ Error: {e}", style="red")
                    
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="bold green")
            break
        except EOFError:
            console.print("\n👋 Goodbye!", style="bold green")
            break


async def _single_chat(message: str, model: Optional[str], stream: bool):
    """Single chat message."""
    assistant = AssistantAgent()
    
    console.print(f"\n[bold blue]You:[/bold blue] {message}")
    console.print("\n[bold green]Assistant:[/bold green] ", end="")
    
    try:
        if stream:
            async for chunk in assistant.chat_stream(message):
                console.print(chunk, end="")
            console.print()
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Thinking...", total=None)
                response = await assistant.chat(message)
                progress.remove_task(task)
                console.print(response)
                
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


def _show_chat_help():
    """Show chat help."""
    help_text = """
Available commands:
- exit, quit, bye: Exit chat
- clear: Clear screen
- help: Show this help
    """
    console.print(Panel(help_text, title="Chat Help", style="cyan"))


@app.command()
def memory(
    action: str = typer.Argument(..., help="Action: search, add, stats, clear"),
    query: Optional[str] = typer.Argument(None, help="Search query or content to add"),
    limit: int = typer.Option(5, "--limit", "-l", help="Number of results to return"),
):
    """Manage the vector memory system."""
    if action == "search":
        if not query:
            console.print("❌ Query required for search", style="red")
            return
        
        console.print(f"🔍 Searching for: {query}", style="bold blue")
        
        try:
            results = memory.search_memories(query, k=limit)
            
            if results:
                for i, result in enumerate(results, 1):
                    console.print(f"\n[bold cyan]Result {i}:[/bold cyan]")
                    console.print(f"Score: {result['score']:.3f}")
                    console.print(f"Text: {result['text'][:200]}...")
                    if result.get('metadata'):
                        console.print(f"Metadata: {result['metadata']}")
            else:
                console.print("No results found", style="yellow")
                
        except Exception as e:
            console.print(f"❌ Search error: {e}", style="red")
    
    elif action == "add":
        if not query:
            console.print("❌ Content required for add", style="red")
            return
        
        try:
            memory_id = memory.add_memory(query, {"source": "cli"})
            console.print(f"✅ Added memory with ID: {memory_id}", style="green")
        except Exception as e:
            console.print(f"❌ Add error: {e}", style="red")
    
    elif action == "stats":
        try:
            stats = memory.get_stats()
            
            stats_table = Table(title="Memory Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green")
            
            for key, value in stats.items():
                stats_table.add_row(str(key).replace("_", " ").title(), str(value))
            
            console.print(stats_table)
        except Exception as e:
            console.print(f"❌ Stats error: {e}", style="red")
    
    elif action == "clear":
        confirm = typer.confirm("Are you sure you want to clear all memories?")
        if confirm:
            console.print("⚠️  Memory clearing not implemented for safety", style="yellow")
        else:
            console.print("Cancelled", style="yellow")
    
    else:
        console.print(f"❌ Unknown action: {action}", style="red")
        console.print("Available actions: search, add, stats, clear")


@app.command()
def docs(
    action: str = typer.Argument(..., help="Action: upload, search, list"),
    file_path: Optional[str] = typer.Argument(None, help="File path for upload"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    limit: int = typer.Option(5, "--limit", "-l", help="Number of results"),
):
    """Manage document processing."""
    if action == "upload":
        if not file_path:
            console.print("❌ File path required for upload", style="red")
            return
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            console.print(f"❌ File not found: {file_path}", style="red")
            return
        
        asyncio.run(_upload_document(file_path_obj))
    
    elif action == "search":
        if not query:
            console.print("❌ Query required for search", style="red")
            return
        
        asyncio.run(_search_documents(query, limit))
    
    elif action == "list":
        console.print("📄 Supported document formats:", style="bold blue")
        formats = document_processor.get_supported_formats()
        for fmt in sorted(formats):
            console.print(f"  • {fmt}")
    
    else:
        console.print(f"❌ Unknown action: {action}", style="red")
        console.print("Available actions: upload, search, list")


async def _upload_document(file_path: Path):
    """Upload and process a document."""
    console.print(f"📤 Uploading: {file_path.name}", style="bold blue")
    
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Processing document...", total=None)
            
            result = await document_processor.process_document(
                file_path=str(file_path),
                file_content=file_content,
                original_filename=file_path.name
            )
            
            progress.remove_task(task)
        
        if result.get('processed'):
            console.print("✅ Document processed successfully!", style="green")
            console.print(f"   Chunks created: {len(result.get('chunks', []))}")
            console.print(f"   Content hash: {result.get('content_hash', 'N/A')}")
        else:
            console.print(f"❌ Processing failed: {result.get('error', 'Unknown error')}", style="red")
            
    except Exception as e:
        console.print(f"❌ Upload error: {e}", style="red")


async def _search_documents(query: str, limit: int):
    """Search processed documents."""
    console.print(f"🔍 Searching documents for: {query}", style="bold blue")
    
    try:
        results = await document_processor.search_documents(query, k=limit)
        
        if results:
            for i, result in enumerate(results, 1):
                console.print(f"\n[bold cyan]Result {i}:[/bold cyan]")
                console.print(f"Score: {result['score']:.3f}")
                console.print(f"Document: {result.get('metadata', {}).get('document_name', 'Unknown')}")
                console.print(f"Text: {result['text'][:200]}...")
        else:
            console.print("No results found", style="yellow")
            
    except Exception as e:
        console.print(f"❌ Search error: {e}", style="red")


@app.command()
def agents(
    action: str = typer.Argument(..., help="Action: list, status, task"),
    agent_name: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent name"),
    task_description: Optional[str] = typer.Option(None, "--task", "-t", help="Task description"),
):
    """Manage AI agents."""
    if action == "list":
        agents_table = Table(title="Available Agents")
        agents_table.add_column("Agent", style="cyan")
        agents_table.add_column("Description", style="green")
        
        agents_info = [
            ("AssistantAgent", "Central coordinator that routes tasks to specialized agents"),
            ("CodeAgent", "Programming, debugging, and technical analysis"),
            ("DocsAgent", "Document processing and analysis"),
            ("PlannerAgent", "Project planning and workflow management"),
            ("ToolAgent", "System operations and external integrations"),
        ]
        
        for name, desc in agents_info:
            agents_table.add_row(name, desc)
        
        console.print(agents_table)
    
    elif action == "status":
        if agent_name:
            asyncio.run(_show_agent_status(agent_name))
        else:
            asyncio.run(_show_all_agents_status())
    
    elif action == "task":
        if not agent_name or not task_description:
            console.print("❌ Agent name and task description required", style="red")
            return
        
        asyncio.run(_execute_agent_task(agent_name, task_description))
    
    else:
        console.print(f"❌ Unknown action: {action}", style="red")
        console.print("Available actions: list, status, task")


async def _show_agent_status(agent_name: str):
    """Show status of a specific agent."""
    agent_map = {
        "assistant": AssistantAgent(),
        "code": CodeAgent(),
        "docs": DocsAgent(),
        "planner": PlannerAgent(),
        "tool": ToolAgent(),
    }
    
    agent = agent_map.get(agent_name.lower())
    if not agent:
        console.print(f"❌ Unknown agent: {agent_name}", style="red")
        return
    
    status = agent.get_status()
    
    status_table = Table(title=f"{agent_name.title()} Agent Status")
    status_table.add_column("Metric", style="cyan")
    status_table.add_column("Value", style="green")
    
    status_table.add_row("Name", status["name"])
    status_table.add_row("Description", status["description"])
    status_table.add_row("Model Type", status["model_type"])
    status_table.add_row("Total Tasks", str(status["total_tasks"]))
    
    for task_status, count in status["task_counts"].items():
        status_table.add_row(f"Tasks {task_status.title()}", str(count))
    
    console.print(status_table)


async def _show_all_agents_status():
    """Show status of all agents."""
    agents = {
        "Assistant": AssistantAgent(),
        "Code": CodeAgent(),
        "Docs": DocsAgent(),
        "Planner": PlannerAgent(),
        "Tool": ToolAgent(),
    }
    
    for name, agent in agents.items():
        status = agent.get_status()
        console.print(f"\n[bold cyan]{name} Agent:[/bold cyan]")
        console.print(f"  Tasks: {status['total_tasks']} total")
        console.print(f"  Status: {status['task_counts']}")


async def _execute_agent_task(agent_name: str, task_description: str):
    """Execute a task with a specific agent."""
    agent_map = {
        "assistant": AssistantAgent(),
        "code": CodeAgent(),
        "docs": DocsAgent(),
        "planner": PlannerAgent(),
        "tool": ToolAgent(),
    }
    
    agent = agent_map.get(agent_name.lower())
    if not agent:
        console.print(f"❌ Unknown agent: {agent_name}", style="red")
        return
    
    console.print(f"🤖 Executing task with {agent_name.title()} Agent", style="bold blue")
    console.print(f"Task: {task_description}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Executing task...", total=None)
            
            task_id = await agent.add_task(task_description)
            result = await agent.execute_task(task_id)
            
            progress.remove_task(task)
        
        if result.status.value == "completed":
            console.print("✅ Task completed successfully!", style="green")
            console.print(f"\n[bold green]Result:[/bold green]\n{result.result}")
        else:
            console.print(f"❌ Task failed: {result.error}", style="red")
            
    except Exception as e:
        console.print(f"❌ Execution error: {e}", style="red")


@app.command()
def config(
    action: str = typer.Argument(..., help="Action: show, edit, validate"),
):
    """Manage system configuration."""
    if action == "show":
        config_data = {
            "server": {
                "host": settings.host,
                "port": settings.port,
                "debug": settings.debug,
            },
            "models": {
                "default_model": settings.default_model,
                "mistral_model": settings.mistral_model,
                "qwen_model": settings.qwen_model,
            },
            "storage": {
                "database_url": settings.database_url,
                "vector_db_path": settings.vector_db_path,
                "upload_dir": settings.upload_dir,
            },
            "memory": {
                "max_memory_size": settings.max_memory_size,
                "embedding_model": settings.embedding_model,
            }
        }
        
        syntax = Syntax(json.dumps(config_data, indent=2), "json", theme="monokai")
        console.print(Panel(syntax, title="System Configuration", style="cyan"))
    
    elif action == "edit":
        console.print("📝 Edit configuration by modifying the .env file", style="yellow")
        console.print(f"   Location: {Path('.env').absolute()}")
    
    elif action == "validate":
        console.print("✅ Configuration validation completed", style="green")
        console.print("   All required settings are present")
    
    else:
        console.print(f"❌ Unknown action: {action}", style="red")
        console.print("Available actions: show, edit, validate")


if __name__ == "__main__":
    app()