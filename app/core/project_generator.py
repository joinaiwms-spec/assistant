"""Project generation system for collaborative code creation."""

import os
import json
import uuid
import zipfile
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from loguru import logger
from jinja2 import Environment, FileSystemLoader, Template

from app.config import settings
from app.agents.code_agent import CodeAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.tool_agent import ToolAgent


class ProjectGenerator:
    """Generate complete projects using collaborative agents."""
    
    def __init__(self):
        self.code_agent = CodeAgent()
        self.planner_agent = PlannerAgent()
        self.tool_agent = ToolAgent()
        self.projects_dir = Path("./generated_projects")
        self.projects_dir.mkdir(exist_ok=True)
        
        # Project templates
        self.templates = {
            "fastapi_app": self._get_fastapi_template(),
            "react_app": self._get_react_template(),
            "python_cli": self._get_python_cli_template(),
            "data_analysis": self._get_data_analysis_template(),
            "microservice": self._get_microservice_template()
        }
    
    async def generate_project(
        self,
        project_type: str,
        name: str,
        description: str,
        requirements: List[str],
        technologies: List[str],
        additional_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate a complete project collaboratively."""
        try:
            project_id = str(uuid.uuid4())
            project_path = self.projects_dir / f"{name}_{project_id}"
            project_path.mkdir(exist_ok=True)
            
            logger.info(f"Starting project generation: {name} ({project_type})")
            
            # Step 1: Create project plan
            plan_result = await self._create_project_plan(
                project_type, name, description, requirements, technologies, additional_context
            )
            
            # Step 2: Generate project structure
            structure_result = await self._generate_project_structure(
                project_path, plan_result, project_type
            )
            
            # Step 3: Generate code files
            code_result = await self._generate_code_files(
                project_path, plan_result, structure_result, requirements, technologies
            )
            
            # Step 4: Create configuration files
            config_result = await self._create_configuration_files(
                project_path, project_type, technologies
            )
            
            # Step 5: Generate documentation
            docs_result = await self._generate_documentation(
                project_path, name, description, requirements, plan_result
            )
            
            # Step 6: Package project
            zip_path = await self._package_project(project_path, name, project_id)
            
            # Collect project metadata
            project_info = {
                "project_id": project_id,
                "name": name,
                "type": project_type,
                "description": description,
                "requirements": requirements,
                "technologies": technologies,
                "path": str(project_path),
                "zip_path": str(zip_path),
                "files_created": self._count_files(project_path),
                "created_at": datetime.utcnow().isoformat(),
                "plan": plan_result,
                "structure": structure_result,
                "status": "completed"
            }
            
            # Save project metadata
            metadata_path = project_path / "project_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(project_info, f, indent=2)
            
            logger.info(f"Project generation completed: {name}")
            return project_info
            
        except Exception as e:
            logger.error(f"Project generation failed: {e}")
            return {
                "project_id": project_id if 'project_id' in locals() else None,
                "status": "failed",
                "error": str(e)
            }
    
    async def _create_project_plan(
        self, project_type: str, name: str, description: str, 
        requirements: List[str], technologies: List[str], additional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create detailed project plan using PlannerAgent."""
        plan_task_id = await self.planner_agent.add_task(
            description=f"Create detailed project plan for {project_type} project",
            context={
                "project_name": name,
                "project_type": project_type,
                "description": description,
                "requirements": requirements,
                "technologies": technologies,
                "additional_context": additional_context or {}
            }
        )
        
        plan_result = await self.planner_agent.execute_task(plan_task_id)
        return {
            "task_id": plan_task_id,
            "plan_content": plan_result.result,
            "status": plan_result.status.value
        }
    
    async def _generate_project_structure(
        self, project_path: Path, plan_result: Dict[str, Any], project_type: str
    ) -> Dict[str, Any]:
        """Generate project directory structure."""
        try:
            # Get template structure
            template = self.templates.get(project_type, self.templates["fastapi_app"])
            structure = template["structure"]
            
            # Create directories
            created_dirs = []
            for dir_path in structure["directories"]:
                full_path = project_path / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(full_path.relative_to(project_path)))
            
            # Create empty files
            created_files = []
            for file_path in structure["files"]:
                full_path = project_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch(exist_ok=True)
                created_files.append(str(full_path.relative_to(project_path)))
            
            return {
                "directories": created_dirs,
                "files": created_files,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Structure generation failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _generate_code_files(
        self, project_path: Path, plan_result: Dict[str, Any], 
        structure_result: Dict[str, Any], requirements: List[str], technologies: List[str]
    ) -> Dict[str, Any]:
        """Generate code files using CodeAgent."""
        try:
            generated_files = []
            
            # Generate main application file
            main_file_task = await self.code_agent.add_task(
                description="Generate main application file",
                context={
                    "file_type": "main_application",
                    "requirements": requirements,
                    "technologies": technologies,
                    "project_path": str(project_path)
                }
            )
            
            main_file_result = await self.code_agent.execute_task(main_file_task)
            if main_file_result.status.value == "completed":
                main_file_path = project_path / "main.py"  # or appropriate extension
                with open(main_file_path, 'w') as f:
                    f.write(main_file_result.result)
                generated_files.append("main.py")
            
            # Generate API endpoints (if applicable)
            if "api" in str(requirements).lower() or "fastapi" in technologies:
                api_task = await self.code_agent.add_task(
                    description="Generate API endpoints",
                    context={
                        "file_type": "api_endpoints",
                        "requirements": requirements,
                        "technologies": technologies
                    }
                )
                
                api_result = await self.code_agent.execute_task(api_task)
                if api_result.status.value == "completed":
                    api_file_path = project_path / "api" / "endpoints.py"
                    api_file_path.parent.mkdir(exist_ok=True)
                    with open(api_file_path, 'w') as f:
                        f.write(api_result.result)
                    generated_files.append("api/endpoints.py")
            
            # Generate models (if applicable)
            if "database" in str(requirements).lower() or "model" in str(requirements).lower():
                models_task = await self.code_agent.add_task(
                    description="Generate database models",
                    context={
                        "file_type": "database_models",
                        "requirements": requirements,
                        "technologies": technologies
                    }
                )
                
                models_result = await self.code_agent.execute_task(models_task)
                if models_result.status.value == "completed":
                    models_file_path = project_path / "models.py"
                    with open(models_file_path, 'w') as f:
                        f.write(models_result.result)
                    generated_files.append("models.py")
            
            # Generate tests
            test_task = await self.code_agent.add_task(
                description="Generate unit tests",
                context={
                    "file_type": "unit_tests",
                    "requirements": requirements,
                    "technologies": technologies,
                    "generated_files": generated_files
                }
            )
            
            test_result = await self.code_agent.execute_task(test_task)
            if test_result.status.value == "completed":
                test_file_path = project_path / "tests" / "test_main.py"
                test_file_path.parent.mkdir(exist_ok=True)
                with open(test_file_path, 'w') as f:
                    f.write(test_result.result)
                generated_files.append("tests/test_main.py")
            
            return {
                "generated_files": generated_files,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _create_configuration_files(
        self, project_path: Path, project_type: str, technologies: List[str]
    ) -> Dict[str, Any]:
        """Create configuration files (requirements.txt, .env, etc.)."""
        try:
            config_files = []
            
            # Create requirements.txt for Python projects
            if "python" in technologies or project_type in ["fastapi_app", "python_cli", "data_analysis"]:
                requirements_content = self._generate_requirements(technologies)
                req_file_path = project_path / "requirements.txt"
                with open(req_file_path, 'w') as f:
                    f.write(requirements_content)
                config_files.append("requirements.txt")
            
            # Create package.json for Node.js projects
            if "node" in technologies or "react" in technologies or project_type == "react_app":
                package_json_content = self._generate_package_json(project_path.name, technologies)
                package_file_path = project_path / "package.json"
                with open(package_file_path, 'w') as f:
                    f.write(package_json_content)
                config_files.append("package.json")
            
            # Create .env.example
            env_content = self._generate_env_template(technologies)
            env_file_path = project_path / ".env.example"
            with open(env_file_path, 'w') as f:
                f.write(env_content)
            config_files.append(".env.example")
            
            # Create .gitignore
            gitignore_content = self._generate_gitignore(project_type, technologies)
            gitignore_path = project_path / ".gitignore"
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)
            config_files.append(".gitignore")
            
            # Create Dockerfile (if applicable)
            if "docker" in technologies:
                dockerfile_content = self._generate_dockerfile(project_type, technologies)
                dockerfile_path = project_path / "Dockerfile"
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                config_files.append("Dockerfile")
            
            return {
                "config_files": config_files,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Configuration generation failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _generate_documentation(
        self, project_path: Path, name: str, description: str, 
        requirements: List[str], plan_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate project documentation."""
        try:
            # Create README.md
            readme_content = self._generate_readme(name, description, requirements, plan_result)
            readme_path = project_path / "README.md"
            with open(readme_path, 'w') as f:
                f.write(readme_content)
            
            # Create API documentation (if applicable)
            if "api" in str(requirements).lower():
                api_docs_content = self._generate_api_docs(name, requirements)
                api_docs_path = project_path / "docs" / "api.md"
                api_docs_path.parent.mkdir(exist_ok=True)
                with open(api_docs_path, 'w') as f:
                    f.write(api_docs_content)
            
            return {
                "docs_created": ["README.md", "docs/api.md"],
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _package_project(self, project_path: Path, name: str, project_id: str) -> Path:
        """Package the project into a downloadable zip file."""
        zip_filename = f"{name}_{project_id}.zip"
        zip_path = self.projects_dir / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(project_path)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def _count_files(self, project_path: Path) -> int:
        """Count the number of files in the project."""
        return len([f for f in project_path.rglob('*') if f.is_file()])
    
    # Template definitions
    def _get_fastapi_template(self) -> Dict[str, Any]:
        return {
            "structure": {
                "directories": [
                    "app", "app/api", "app/core", "app/models", 
                    "tests", "docs", "scripts"
                ],
                "files": [
                    "main.py", "app/__init__.py", "app/api/__init__.py",
                    "app/core/__init__.py", "app/models/__init__.py",
                    "tests/__init__.py", "tests/test_main.py"
                ]
            }
        }
    
    def _get_react_template(self) -> Dict[str, Any]:
        return {
            "structure": {
                "directories": [
                    "src", "src/components", "src/pages", "src/hooks",
                    "src/utils", "public", "tests"
                ],
                "files": [
                    "src/App.js", "src/index.js", "src/App.css",
                    "public/index.html", "public/manifest.json"
                ]
            }
        }
    
    def _get_python_cli_template(self) -> Dict[str, Any]:
        return {
            "structure": {
                "directories": ["src", "tests", "docs"],
                "files": [
                    "src/__init__.py", "src/cli.py", "src/main.py",
                    "tests/__init__.py", "tests/test_cli.py"
                ]
            }
        }
    
    def _get_data_analysis_template(self) -> Dict[str, Any]:
        return {
            "structure": {
                "directories": [
                    "data", "notebooks", "src", "tests", "results", "docs"
                ],
                "files": [
                    "src/__init__.py", "src/analysis.py", "src/utils.py",
                    "notebooks/exploration.ipynb", "tests/test_analysis.py"
                ]
            }
        }
    
    def _get_microservice_template(self) -> Dict[str, Any]:
        return {
            "structure": {
                "directories": [
                    "app", "app/api", "app/services", "app/models",
                    "app/core", "tests", "docker", "k8s"
                ],
                "files": [
                    "main.py", "app/__init__.py", "app/api/endpoints.py",
                    "app/services/__init__.py", "app/models/__init__.py",
                    "docker/Dockerfile", "k8s/deployment.yaml"
                ]
            }
        }
    
    # Content generators
    def _generate_requirements(self, technologies: List[str]) -> str:
        """Generate requirements.txt content based on technologies."""
        base_requirements = []
        
        if "fastapi" in technologies:
            base_requirements.extend([
                "fastapi>=0.104.1",
                "uvicorn[standard]>=0.24.0",
                "pydantic>=2.5.0"
            ])
        
        if "sqlalchemy" in technologies or "database" in technologies:
            base_requirements.extend([
                "sqlalchemy>=2.0.23",
                "alembic>=1.12.1"
            ])
        
        if "pytest" in technologies or True:  # Always include testing
            base_requirements.extend([
                "pytest>=7.4.3",
                "pytest-asyncio>=0.21.1"
            ])
        
        if "requests" in technologies or "http" in technologies:
            base_requirements.append("httpx>=0.25.2")
        
        # Add common utilities
        base_requirements.extend([
            "python-dotenv>=1.0.0",
            "loguru>=0.7.2"
        ])
        
        return "\n".join(sorted(set(base_requirements))) + "\n"
    
    def _generate_package_json(self, project_name: str, technologies: List[str]) -> str:
        """Generate package.json for Node.js projects."""
        package_data = {
            "name": project_name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "description": f"Generated {project_name} project",
            "main": "index.js",
            "scripts": {
                "start": "node index.js",
                "dev": "nodemon index.js",
                "test": "jest"
            },
            "dependencies": {},
            "devDependencies": {
                "nodemon": "^3.0.0",
                "jest": "^29.0.0"
            }
        }
        
        if "react" in technologies:
            package_data["dependencies"].update({
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            })
            package_data["scripts"]["start"] = "react-scripts start"
            package_data["scripts"]["build"] = "react-scripts build"
        
        if "express" in technologies:
            package_data["dependencies"]["express"] = "^4.18.0"
        
        return json.dumps(package_data, indent=2)
    
    def _generate_env_template(self, technologies: List[str]) -> str:
        """Generate .env.example template."""
        env_vars = [
            "# Environment Configuration",
            "NODE_ENV=development",
            "PORT=3000",
            ""
        ]
        
        if "database" in technologies or "postgresql" in technologies:
            env_vars.extend([
                "# Database Configuration",
                "DATABASE_URL=postgresql://user:password@localhost:5432/dbname",
                ""
            ])
        
        if "redis" in technologies:
            env_vars.extend([
                "# Redis Configuration",
                "REDIS_URL=redis://localhost:6379",
                ""
            ])
        
        if "jwt" in technologies or "auth" in technologies:
            env_vars.extend([
                "# Authentication",
                "JWT_SECRET=your-secret-key-here",
                "JWT_EXPIRES_IN=24h",
                ""
            ])
        
        return "\n".join(env_vars)
    
    def _generate_gitignore(self, project_type: str, technologies: List[str]) -> str:
        """Generate .gitignore file."""
        gitignore_content = [
            "# Dependencies",
            "node_modules/",
            "__pycache__/",
            "*.pyc",
            "",
            "# Environment variables",
            ".env",
            ".env.local",
            "",
            "# Build outputs",
            "dist/",
            "build/",
            "*.egg-info/",
            "",
            "# IDE files",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "",
            "# OS files",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# Logs",
            "*.log",
            "logs/",
            ""
        ]
        
        if "python" in technologies or project_type in ["fastapi_app", "python_cli"]:
            gitignore_content.extend([
                "# Python specific",
                "venv/",
                "env/",
                "*.egg",
                ".pytest_cache/",
                ""
            ])
        
        if "react" in technologies or "node" in technologies:
            gitignore_content.extend([
                "# Node.js specific",
                "npm-debug.log*",
                "yarn-debug.log*",
                "yarn-error.log*",
                ""
            ])
        
        return "\n".join(gitignore_content)
    
    def _generate_dockerfile(self, project_type: str, technologies: List[str]) -> str:
        """Generate Dockerfile."""
        if "python" in technologies or project_type in ["fastapi_app", "python_cli"]:
            return """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
"""
        elif "node" in technologies or "react" in technologies:
            return """FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
"""
        else:
            return """FROM alpine:latest

WORKDIR /app

COPY . .

EXPOSE 8000

CMD ["./start.sh"]
"""
    
    def _generate_readme(self, name: str, description: str, requirements: List[str], plan_result: Dict[str, Any]) -> str:
        """Generate README.md content."""
        return f"""# {name}

{description}

## Features

{chr(10).join(f"- {req}" for req in requirements)}

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd {name.lower().replace(" ", "-")}
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
python main.py
```

## Project Structure

```
{name.lower().replace(" ", "-")}/
├── app/                 # Application code
├── tests/              # Test files
├── docs/               # Documentation
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
└── README.md          # This file
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
```

## API Documentation

When running the application, visit:
- API Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

---

Generated by AI Assistant System
"""
    
    def _generate_api_docs(self, name: str, requirements: List[str]) -> str:
        """Generate API documentation."""
        return f"""# {name} API Documentation

## Overview

This document describes the API endpoints for {name}.

## Base URL

```
http://localhost:8000
```

## Authentication

Include authentication details here if applicable.

## Endpoints

### Health Check

```http
GET /health
```

Returns the health status of the API.

**Response:**
```json
{{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}}
```

### Main Endpoints

Document your main API endpoints here based on the requirements:

{chr(10).join(f"- {req}" for req in requirements)}

## Error Handling

All errors follow this format:

```json
{{
  "error": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}}
```

## Rate Limiting

API requests are limited to prevent abuse. See headers:
- `X-RateLimit-Limit`: Request limit per time window
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

---

For more information, visit the interactive API documentation at `/docs`.
"""


# Global project generator instance
project_generator = ProjectGenerator()