"""Tool Agent - Specialized agent for system operations and external integrations."""

import os
import subprocess
import shutil
import zipfile
from typing import Dict, List, Any, Optional
from pathlib import Path

from loguru import logger

from app.agents.base import BaseAgent, AgentTask
from app.core.llm import ChatMessage, ModelType


class ToolAgent(BaseAgent):
    """Agent specialized in system operations, file management, and external tool integrations."""
    
    def __init__(self):
        super().__init__(
            name="ToolAgent",
            description="Specialized agent for system operations, file management, and external tool integrations",
            model_type=ModelType.DEFAULT
        )
    
    def _get_system_prompt(self) -> str:
        return """You are ToolAgent, a specialized AI agent focused on system operations and tool integrations. Your expertise includes:

1. File system operations and management
2. System command execution and automation
3. External tool integration and API calls
4. Project packaging and deployment
5. Environment setup and configuration
6. Data processing and transformation
7. Backup and archival operations
8. System monitoring and diagnostics

When handling tool-related tasks:
- Execute operations safely and securely
- Validate inputs and handle errors gracefully
- Provide clear feedback on operation results
- Follow best practices for system operations
- Maintain security and access controls
- Log operations for audit trails
- Handle cross-platform compatibility
- Optimize for performance and efficiency

Always prioritize system security and data integrity in all operations."""
    
    async def _execute_task(self, task: AgentTask) -> str:
        """Execute a tool-related task."""
        try:
            task_type = self._classify_task(task.description)
            
            if task_type == "file_operations":
                return await self._handle_file_operations(task)
            elif task_type == "system_commands":
                return await self._execute_system_commands(task)
            elif task_type == "project_packaging":
                return await self._package_project(task)
            elif task_type == "environment_setup":
                return await self._setup_environment(task)
            elif task_type == "data_processing":
                return await self._process_data(task)
            else:
                return await self._handle_general_tool_task(task)
                
        except Exception as e:
            logger.error(f"Error in ToolAgent task execution: {e}")
            raise
    
    def _classify_task(self, description: str) -> str:
        """Classify the type of tool task."""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["file", "directory", "folder", "copy", "move"]):
            return "file_operations"
        elif any(keyword in description_lower for keyword in ["command", "execute", "run", "script"]):
            return "system_commands"
        elif any(keyword in description_lower for keyword in ["package", "zip", "archive", "bundle"]):
            return "project_packaging"
        elif any(keyword in description_lower for keyword in ["setup", "install", "configure", "environment"]):
            return "environment_setup"
        elif any(keyword in description_lower for keyword in ["process", "transform", "convert", "data"]):
            return "data_processing"
        else:
            return "general"
    
    async def _handle_file_operations(self, task: AgentTask) -> str:
        """Handle file system operations."""
        operation = task.context.get("operation", "")
        source_path = task.context.get("source_path", "")
        target_path = task.context.get("target_path", "")
        
        try:
            if operation.lower() == "copy":
                result = self._copy_files(source_path, target_path)
            elif operation.lower() == "move":
                result = self._move_files(source_path, target_path)
            elif operation.lower() == "delete":
                result = self._delete_files(source_path)
            elif operation.lower() == "create_directory":
                result = self._create_directory(source_path)
            elif operation.lower() == "list":
                result = self._list_directory(source_path)
            else:
                result = f"Unknown file operation: {operation}"
            
            return f"File operation completed: {result}"
            
        except Exception as e:
            logger.error(f"File operation error: {e}")
            return f"File operation failed: {str(e)}"
    
    async def _execute_system_commands(self, task: AgentTask) -> str:
        """Execute system commands safely."""
        commands = task.context.get("commands", [])
        working_directory = task.context.get("working_directory", ".")
        
        if not commands:
            return "No commands specified for execution."
        
        results = []
        
        for command in commands:
            try:
                # Basic security check
                if self._is_safe_command(command):
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        cwd=working_directory,
                        timeout=60  # 60 second timeout
                    )
                    
                    results.append({
                        "command": command,
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "success": result.returncode == 0
                    })
                else:
                    results.append({
                        "command": command,
                        "error": "Command rejected for security reasons",
                        "success": False
                    })
                    
            except subprocess.TimeoutExpired:
                results.append({
                    "command": command,
                    "error": "Command timed out",
                    "success": False
                })
            except Exception as e:
                results.append({
                    "command": command,
                    "error": str(e),
                    "success": False
                })
        
        # Format results
        formatted_results = "System command execution results:\n\n"
        for result in results:
            formatted_results += f"Command: {result['command']}\n"
            if result.get('success'):
                formatted_results += f"Status: Success (exit code: {result.get('returncode', 'N/A')})\n"
                if result.get('stdout'):
                    formatted_results += f"Output: {result['stdout']}\n"
            else:
                formatted_results += f"Status: Failed\n"
                if result.get('stderr'):
                    formatted_results += f"Error: {result['stderr']}\n"
                elif result.get('error'):
                    formatted_results += f"Error: {result['error']}\n"
            formatted_results += "\n"
        
        return formatted_results
    
    async def _package_project(self, task: AgentTask) -> str:
        """Package project files into a downloadable archive."""
        project_path = task.context.get("project_path", ".")
        output_path = task.context.get("output_path", "./project.zip")
        include_patterns = task.context.get("include_patterns", ["*"])
        exclude_patterns = task.context.get("exclude_patterns", [
            "*.pyc", "__pycache__", ".git", "node_modules", ".env"
        ])
        
        try:
            zip_path = self._create_project_zip(
                project_path, output_path, include_patterns, exclude_patterns
            )
            
            file_size = os.path.getsize(zip_path)
            file_count = self._count_files_in_zip(zip_path)
            
            return f"""Project packaging completed successfully:
            
Archive: {zip_path}
Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)
Files: {file_count} files included
            
The project has been packaged and is ready for download."""
            
        except Exception as e:
            logger.error(f"Project packaging error: {e}")
            return f"Project packaging failed: {str(e)}"
    
    async def _setup_environment(self, task: AgentTask) -> str:
        """Set up development environment."""
        environment_type = task.context.get("environment_type", "python")
        requirements = task.context.get("requirements", [])
        project_path = task.context.get("project_path", ".")
        
        setup_results = []
        
        try:
            if environment_type.lower() == "python":
                setup_results.extend(self._setup_python_environment(project_path, requirements))
            elif environment_type.lower() == "node":
                setup_results.extend(self._setup_node_environment(project_path, requirements))
            else:
                setup_results.append(f"Environment type '{environment_type}' not supported")
            
            # Format results
            formatted_results = "Environment setup results:\n\n"
            for result in setup_results:
                formatted_results += f"- {result}\n"
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Environment setup error: {e}")
            return f"Environment setup failed: {str(e)}"
    
    async def _process_data(self, task: AgentTask) -> str:
        """Process and transform data."""
        data_source = task.context.get("data_source", "")
        processing_type = task.context.get("processing_type", "")
        output_format = task.context.get("output_format", "json")
        
        try:
            if processing_type.lower() == "csv_to_json":
                result = self._convert_csv_to_json(data_source)
            elif processing_type.lower() == "json_to_csv":
                result = self._convert_json_to_csv(data_source)
            elif processing_type.lower() == "validate":
                result = self._validate_data_format(data_source)
            else:
                result = f"Data processing type '{processing_type}' not supported"
            
            return f"Data processing completed: {result}"
            
        except Exception as e:
            logger.error(f"Data processing error: {e}")
            return f"Data processing failed: {str(e)}"
    
    async def _handle_general_tool_task(self, task: AgentTask) -> str:
        """Handle general tool-related tasks."""
        memories = await self.get_relevant_memories(task.description)
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant tool usage experience:\n"
            for mem in memories[:3]:
                memory_context += f"- {mem['text'][:200]}...\n"
        
        general_prompt = f"""
        Handle this tool-related task:
        
        Task: {task.description}
        Context: {task.context}
        {memory_context}
        
        Provide guidance on how to accomplish this task using appropriate tools and methods.
        Include specific commands, configurations, or procedures where applicable.
        Focus on practical, actionable solutions.
        """
        
        messages = [ChatMessage(role="user", content=general_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    # Helper methods for file operations
    def _copy_files(self, source: str, target: str) -> str:
        """Copy files or directories."""
        source_path = Path(source)
        target_path = Path(target)
        
        if source_path.is_file():
            shutil.copy2(source_path, target_path)
            return f"Copied file {source} to {target}"
        elif source_path.is_dir():
            shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            return f"Copied directory {source} to {target}"
        else:
            return f"Source path {source} does not exist"
    
    def _move_files(self, source: str, target: str) -> str:
        """Move files or directories."""
        shutil.move(source, target)
        return f"Moved {source} to {target}"
    
    def _delete_files(self, path: str) -> str:
        """Delete files or directories."""
        path_obj = Path(path)
        if path_obj.is_file():
            path_obj.unlink()
            return f"Deleted file {path}"
        elif path_obj.is_dir():
            shutil.rmtree(path_obj)
            return f"Deleted directory {path}"
        else:
            return f"Path {path} does not exist"
    
    def _create_directory(self, path: str) -> str:
        """Create directory."""
        Path(path).mkdir(parents=True, exist_ok=True)
        return f"Created directory {path}"
    
    def _list_directory(self, path: str) -> str:
        """List directory contents."""
        path_obj = Path(path)
        if path_obj.is_dir():
            contents = list(path_obj.iterdir())
            return f"Directory {path} contains {len(contents)} items: {[item.name for item in contents]}"
        else:
            return f"Path {path} is not a directory"
    
    def _is_safe_command(self, command: str) -> bool:
        """Basic security check for commands."""
        dangerous_commands = [
            "rm -rf", "del", "format", "fdisk", "mkfs",
            "shutdown", "reboot", "halt", "sudo rm",
            "dd if=", ":(){ :|:& };:"  # Fork bomb
        ]
        
        command_lower = command.lower()
        return not any(dangerous in command_lower for dangerous in dangerous_commands)
    
    def _create_project_zip(self, project_path: str, output_path: str, 
                           include_patterns: List[str], exclude_patterns: List[str]) -> str:
        """Create a zip file of the project."""
        project_path_obj = Path(project_path)
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_path_obj.rglob('*'):
                if file_path.is_file():
                    # Check if file should be included
                    relative_path = file_path.relative_to(project_path_obj)
                    
                    # Skip excluded patterns
                    if any(relative_path.match(pattern) for pattern in exclude_patterns):
                        continue
                    
                    # Include if matches include patterns
                    if any(relative_path.match(pattern) for pattern in include_patterns):
                        zipf.write(file_path, relative_path)
        
        return output_path
    
    def _count_files_in_zip(self, zip_path: str) -> int:
        """Count files in a zip archive."""
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            return len(zipf.filelist)
    
    def _setup_python_environment(self, project_path: str, requirements: List[str]) -> List[str]:
        """Set up Python environment."""
        results = []
        
        # Create virtual environment
        venv_path = Path(project_path) / "venv"
        if not venv_path.exists():
            subprocess.run(["python", "-m", "venv", str(venv_path)], check=True)
            results.append("Created Python virtual environment")
        
        # Install requirements
        if requirements:
            pip_path = venv_path / "bin" / "pip" if os.name != 'nt' else venv_path / "Scripts" / "pip.exe"
            for req in requirements:
                subprocess.run([str(pip_path), "install", req], check=True)
                results.append(f"Installed {req}")
        
        return results
    
    def _setup_node_environment(self, project_path: str, requirements: List[str]) -> List[str]:
        """Set up Node.js environment."""
        results = []
        
        # Initialize npm if package.json doesn't exist
        package_json = Path(project_path) / "package.json"
        if not package_json.exists():
            subprocess.run(["npm", "init", "-y"], cwd=project_path, check=True)
            results.append("Initialized npm project")
        
        # Install packages
        if requirements:
            for req in requirements:
                subprocess.run(["npm", "install", req], cwd=project_path, check=True)
                results.append(f"Installed {req}")
        
        return results
    
    def _convert_csv_to_json(self, csv_path: str) -> str:
        """Convert CSV to JSON."""
        # This would need pandas or csv module implementation
        return f"CSV to JSON conversion for {csv_path} would be implemented here"
    
    def _convert_json_to_csv(self, json_path: str) -> str:
        """Convert JSON to CSV."""
        # This would need pandas or csv module implementation
        return f"JSON to CSV conversion for {json_path} would be implemented here"
    
    def _validate_data_format(self, data_path: str) -> str:
        """Validate data format."""
        path_obj = Path(data_path)
        if not path_obj.exists():
            return f"File {data_path} does not exist"
        
        file_size = path_obj.stat().st_size
        return f"File {data_path} exists, size: {file_size} bytes"