"""Planner Agent - Specialized agent for project planning and workflow management."""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from loguru import logger

from app.agents.base import BaseAgent, AgentTask
from app.core.llm import ChatMessage, ModelType


class PlannerAgent(BaseAgent):
    """Agent specialized in project planning, workflow management, and task breakdown."""
    
    def __init__(self):
        super().__init__(
            name="PlannerAgent",
            description="Specialized agent for project planning, workflow management, and task breakdown",
            model_type=ModelType.DEFAULT
        )
    
    def _get_system_prompt(self) -> str:
        return """You are PlannerAgent, a specialized AI agent focused on project planning and workflow management. Your expertise includes:

1. Project planning and roadmap creation
2. Task breakdown and work estimation
3. Timeline and milestone planning
4. Resource allocation and dependency management
5. Risk assessment and mitigation strategies
6. Workflow optimization and process design
7. Progress tracking and reporting
8. Agile and traditional project management methodologies

When handling planning tasks:
- Create realistic and achievable plans
- Consider dependencies and constraints
- Provide clear timelines and milestones
- Include risk assessments and mitigation strategies
- Break down complex projects into manageable tasks
- Consider resource requirements and availability
- Provide actionable next steps
- Use appropriate project management frameworks

Always ensure plans are practical, well-structured, and adaptable to changing requirements."""
    
    async def _execute_task(self, task: AgentTask) -> str:
        """Execute a planning-related task."""
        try:
            task_type = self._classify_task(task.description)
            
            if task_type == "project_planning":
                return await self._create_project_plan(task)
            elif task_type == "task_breakdown":
                return await self._break_down_tasks(task)
            elif task_type == "timeline_creation":
                return await self._create_timeline(task)
            elif task_type == "risk_assessment":
                return await self._assess_risks(task)
            elif task_type == "workflow_design":
                return await self._design_workflow(task)
            else:
                return await self._handle_general_planning_task(task)
                
        except Exception as e:
            logger.error(f"Error in PlannerAgent task execution: {e}")
            raise
    
    def _classify_task(self, description: str) -> str:
        """Classify the type of planning task."""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["project plan", "roadmap", "strategy"]):
            return "project_planning"
        elif any(keyword in description_lower for keyword in ["break down", "tasks", "subtasks"]):
            return "task_breakdown"
        elif any(keyword in description_lower for keyword in ["timeline", "schedule", "milestone"]):
            return "timeline_creation"
        elif any(keyword in description_lower for keyword in ["risk", "assessment", "mitigation"]):
            return "risk_assessment"
        elif any(keyword in description_lower for keyword in ["workflow", "process", "procedure"]):
            return "workflow_design"
        else:
            return "general"
    
    async def _create_project_plan(self, task: AgentTask) -> str:
        """Create a comprehensive project plan."""
        project_description = task.context.get("project_description", task.description)
        requirements = task.context.get("requirements", [])
        constraints = task.context.get("constraints", [])
        
        # Get relevant memories for similar projects
        memories = await self.get_relevant_memories(f"project plan {project_description}")
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant experience from similar projects:\n"
            for mem in memories[:2]:
                memory_context += f"- {mem['text'][:200]}...\n"
        
        planning_prompt = f"""
        Create a comprehensive project plan for the following:
        
        Project: {project_description}
        Requirements: {json.dumps(requirements, indent=2)}
        Constraints: {json.dumps(constraints, indent=2)}
        {memory_context}
        
        Please provide a detailed project plan including:
        
        1. **Project Overview**
           - Objectives and goals
           - Success criteria
           - Key stakeholders
        
        2. **Scope and Deliverables**
           - In-scope items
           - Out-of-scope items
           - Key deliverables
        
        3. **Work Breakdown Structure**
           - Major phases
           - Key tasks and subtasks
           - Dependencies
        
        4. **Timeline and Milestones**
           - Project phases with durations
           - Key milestones and deadlines
           - Critical path
        
        5. **Resource Requirements**
           - Team composition
           - Skills required
           - Tools and technologies
        
        6. **Risk Assessment**
           - Potential risks
           - Impact and probability
           - Mitigation strategies
        
        7. **Communication Plan**
           - Reporting structure
           - Meeting cadence
           - Status updates
        
        Format the plan clearly and make it actionable.
        """
        
        messages = [ChatMessage(role="user", content=planning_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _break_down_tasks(self, task: AgentTask) -> str:
        """Break down complex tasks into manageable subtasks."""
        main_task = task.context.get("main_task", task.description)
        complexity_level = task.context.get("complexity", "medium")
        
        breakdown_prompt = f"""
        Break down the following task into manageable subtasks:
        
        Main Task: {main_task}
        Complexity Level: {complexity_level}
        Context: {json.dumps(task.context, indent=2)}
        
        Please provide:
        
        1. **Task Analysis**
           - Task complexity assessment
           - Key components identification
           - Dependencies mapping
        
        2. **Subtask Breakdown**
           For each subtask provide:
           - Clear description
           - Estimated effort (hours/days)
           - Required skills/expertise
           - Dependencies on other subtasks
           - Priority level (High/Medium/Low)
           - Acceptance criteria
        
        3. **Execution Order**
           - Recommended sequence
           - Parallel execution opportunities
           - Critical path identification
        
        4. **Resource Allocation**
           - Skill requirements per subtask
           - Estimated time per subtask
           - Potential bottlenecks
        
        Make the breakdown practical and actionable.
        """
        
        messages = [ChatMessage(role="user", content=breakdown_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _create_timeline(self, task: AgentTask) -> str:
        """Create project timeline with milestones."""
        project_scope = task.context.get("scope", task.description)
        duration = task.context.get("duration", "Not specified")
        team_size = task.context.get("team_size", "Not specified")
        
        timeline_prompt = f"""
        Create a detailed timeline for the following project:
        
        Project Scope: {project_scope}
        Duration: {duration}
        Team Size: {team_size}
        Context: {json.dumps(task.context, indent=2)}
        
        Please provide:
        
        1. **Timeline Overview**
           - Total project duration
           - Major phases with dates
           - Key milestones
        
        2. **Detailed Schedule**
           - Week-by-week breakdown
           - Task assignments
           - Dependencies and blockers
        
        3. **Milestone Planning**
           - Milestone descriptions
           - Deliverables for each milestone
           - Success criteria
           - Review points
        
        4. **Buffer and Risk Management**
           - Buffer time allocation
           - Risk mitigation time
           - Contingency plans
        
        5. **Resource Timeline**
           - Team member allocation
           - Skill requirements over time
           - Peak resource periods
        
        Present the timeline in a clear, visual format with specific dates.
        """
        
        messages = [ChatMessage(role="user", content=timeline_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _assess_risks(self, task: AgentTask) -> str:
        """Assess project risks and create mitigation strategies."""
        project_context = task.context.get("project_context", task.description)
        project_type = task.context.get("project_type", "general")
        
        risk_prompt = f"""
        Conduct a comprehensive risk assessment for the following project:
        
        Project Context: {project_context}
        Project Type: {project_type}
        Additional Context: {json.dumps(task.context, indent=2)}
        
        Please provide:
        
        1. **Risk Identification**
           - Technical risks
           - Resource risks
           - Timeline risks
           - External risks
           - Quality risks
        
        2. **Risk Analysis**
           For each risk provide:
           - Risk description
           - Probability (High/Medium/Low)
           - Impact (High/Medium/Low)
           - Risk score (Probability × Impact)
           - Potential consequences
        
        3. **Risk Prioritization**
           - Critical risks (immediate attention)
           - High priority risks
           - Medium priority risks
           - Low priority risks
        
        4. **Mitigation Strategies**
           For each significant risk:
           - Prevention strategies
           - Mitigation actions
           - Contingency plans
           - Responsible parties
           - Monitoring indicators
        
        5. **Risk Monitoring Plan**
           - Risk review schedule
           - Early warning indicators
           - Escalation procedures
        
        Focus on actionable strategies and realistic assessments.
        """
        
        messages = [ChatMessage(role="user", content=risk_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _design_workflow(self, task: AgentTask) -> str:
        """Design workflow and process procedures."""
        workflow_purpose = task.context.get("purpose", task.description)
        stakeholders = task.context.get("stakeholders", [])
        
        workflow_prompt = f"""
        Design a workflow for the following purpose:
        
        Workflow Purpose: {workflow_purpose}
        Stakeholders: {json.dumps(stakeholders, indent=2)}
        Context: {json.dumps(task.context, indent=2)}
        
        Please provide:
        
        1. **Workflow Overview**
           - Purpose and objectives
           - Key stakeholders and roles
           - Success metrics
        
        2. **Process Steps**
           For each step provide:
           - Step description
           - Input requirements
           - Actions to be taken
           - Output/deliverables
           - Responsible party
           - Estimated duration
        
        3. **Decision Points**
           - Decision criteria
           - Alternative paths
           - Approval processes
           - Escalation procedures
        
        4. **Tools and Resources**
           - Required tools/systems
           - Templates and documentation
           - Communication channels
        
        5. **Quality Control**
           - Checkpoints and reviews
           - Quality criteria
           - Validation procedures
        
        6. **Optimization Opportunities**
           - Automation possibilities
           - Efficiency improvements
           - Bottleneck elimination
        
        Design the workflow to be efficient, clear, and scalable.
        """
        
        messages = [ChatMessage(role="user", content=workflow_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _handle_general_planning_task(self, task: AgentTask) -> str:
        """Handle general planning-related tasks."""
        memories = await self.get_relevant_memories(task.description)
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant planning experience:\n"
            for mem in memories[:3]:
                memory_context += f"- {mem['text'][:200]}...\n"
        
        general_prompt = f"""
        Handle this planning-related task:
        
        Task: {task.description}
        Context: {json.dumps(task.context, indent=2)}
        {memory_context}
        
        Provide a comprehensive planning response that addresses the task requirements.
        Include structured analysis, actionable recommendations, and clear next steps.
        Use appropriate project management frameworks and best practices.
        """
        
        messages = [ChatMessage(role="user", content=general_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    def generate_project_template(self, project_type: str) -> Dict[str, Any]:
        """Generate a project template based on project type."""
        templates = {
            "software_development": {
                "phases": ["Planning", "Design", "Development", "Testing", "Deployment", "Maintenance"],
                "key_deliverables": ["Requirements", "Architecture", "Code", "Test Results", "Documentation"],
                "typical_roles": ["Project Manager", "Developer", "Designer", "QA Engineer", "DevOps"],
                "common_risks": ["Scope creep", "Technical debt", "Resource constraints", "Integration issues"]
            },
            "marketing_campaign": {
                "phases": ["Strategy", "Creative", "Production", "Launch", "Analysis"],
                "key_deliverables": ["Campaign Strategy", "Creative Assets", "Media Plan", "Launch Materials", "Performance Report"],
                "typical_roles": ["Campaign Manager", "Creative Director", "Content Creator", "Media Buyer", "Analyst"],
                "common_risks": ["Budget overrun", "Timeline delays", "Creative approval", "Market changes"]
            },
            "data_analysis": {
                "phases": ["Data Collection", "Cleaning", "Analysis", "Visualization", "Reporting"],
                "key_deliverables": ["Data Sources", "Clean Dataset", "Analysis Results", "Visualizations", "Final Report"],
                "typical_roles": ["Data Analyst", "Data Engineer", "Statistician", "Business Analyst"],
                "common_risks": ["Data quality", "Tool limitations", "Interpretation errors", "Stakeholder alignment"]
            }
        }
        
        return templates.get(project_type, {
            "phases": ["Planning", "Execution", "Review"],
            "key_deliverables": ["Plan", "Deliverables", "Report"],
            "typical_roles": ["Project Manager", "Team Members", "Stakeholders"],
            "common_risks": ["Resource constraints", "Timeline pressure", "Scope changes"]
        })