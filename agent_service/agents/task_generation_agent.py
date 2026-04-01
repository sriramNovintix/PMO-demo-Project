"""
Task Generation Agent
Generates actionable tasks from weekly goals
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, invoke_with_prompt


class TaskGenerationAgent:
    """
    Task Generation Agent - Autonomous
    Breaks down weekly goals into specific, actionable tasks
    """
    
    def __init__(self):
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Task Generation Agent.
Your role is to break down weekly goals into specific, actionable tasks.

For each task, provide:
1. Title (clear, action-oriented)
2. Description (what needs to be done)
3. Estimated hours
4. Required skills
5. Priority (high/medium/low)
6. Dependencies (if any)

Generate 5-10 tasks that cover the weekly goal comprehensively.

Respond in JSON format:
{{
    "tasks": [
        {{
            "title": "Task title",
            "description": "Detailed description",
            "estimated_hours": 8,
            "required_skills": ["skill1", "skill2"],
            "priority": "high|medium|low",
            "dependencies": []
        }}
    ],
    "total_estimated_hours": 40
}}"""),
            ("human", """Project: {project_name}

Weekly Goal: {weekly_goal}

Generate actionable tasks.""")
        ])
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task generation - autonomous method
        Generates tasks and saves to database
        
        Args:
            state: Current state with project_name and weekly_goal
        
        Returns:
            Result with generated tasks and state updates
        """
        try:
            # Check if we have required information
            weekly_goal = state.get("weekly_goal")
            if not weekly_goal:
                return {
                    "success": False,
                    "error": "Missing weekly goal",
                    "tasks": [],
                    "state_updates": {},
                    "message": "Please provide a weekly goal first"
                }
            
            # Use project name or default
            project_name = state.get("project_name") or "Unnamed Project"
            
            # Generate tasks
            result = self.generate_tasks(project_name, weekly_goal)
            
            if not result["success"]:
                return {
                    "success": False,
                    "error": result.get("error"),
                    "tasks": [],
                    "state_updates": {},
                    "message": f"Failed to generate tasks: {result.get('error')}"
                }
            
            # Save tasks to database
            from database import db
            session_id = state.get("session_id")
            tasks = result["tasks"]
            
            for task in tasks:
                task_data = {
                    "title": task.get("title", "Untitled Task"),
                    "description": task.get("description", ""),
                    "assigned_to": None,
                    "assigned_to_email": None,
                    "estimated_hours": task.get("estimated_hours", 0),
                    "session_id": session_id,
                    "project_id": project_name
                }
                
                db_result = db.create_task(task_data)
                if db_result["success"]:
                    task["task_id"] = db_result["task_id"]
            
            return {
                "success": True,
                "tasks": tasks,
                "total_estimated_hours": result["total_estimated_hours"],
                "state_updates": {
                    "generated_tasks": tasks
                },
                "message": f"Generated {len(tasks)} tasks ({result['total_estimated_hours']}h total)"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tasks": [],
                "state_updates": {},
                "message": f"Error: {str(e)}"
            }
    
    def generate_tasks(self, project_name: str, weekly_goal: str) -> Dict[str, Any]:
        """
        Generate tasks from weekly goal
        
        Args:
            project_name: Name of the project
            weekly_goal: Weekly goal description
        
        Returns:
            List of generated tasks
        """
        try:
            response = invoke_with_prompt(
                self.prompt,
                self.llm,
                project_name=project_name,
                weekly_goal=weekly_goal
            )
            
            # Parse response
            import json
            content = response.content
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            
            return {
                "success": True,
                "tasks": result.get("tasks", []),
                "total_estimated_hours": result.get("total_estimated_hours", 0)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tasks": []
            }


# Global instance
task_generation_agent = TaskGenerationAgent()
