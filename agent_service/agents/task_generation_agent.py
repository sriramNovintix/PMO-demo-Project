"""
Task Generation Agent
Generates actionable tasks from weekly goals
Standalone runnable agent with state management
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, invoke_with_prompt
from agents.base_agent import BaseAgent
import json


class TaskGenerationAgent(BaseAgent):
    """
    Task Generation Agent
    Breaks down weekly goals into specific, actionable tasks
    """
    
    def __init__(self):
        super().__init__("task_generation_agent")
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
    
    def generate_tasks(self, project_name: str, weekly_goal: str) -> Dict[str, Any]:
        """
        Generate tasks from weekly goal
        
        Args:
            project_name: Name of the project
            weekly_goal: Weekly goal description
        
        Returns:
            List of generated tasks with state updates
        """
        try:
            # Log input
            self.log_action("generate_tasks_start", "processing", project_name=project_name, weekly_goal=weekly_goal)
            
            response = invoke_with_prompt(
                self.prompt,
                self.llm,
                project_name=project_name,
                weekly_goal=weekly_goal
            )
            
            # Parse response
            content = response.content
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            
            # Log success
            self.log_action("generate_tasks_complete", "success", tasks_count=len(result.get("tasks", [])))
            
            return {
                "success": True,
                "tasks": result.get("tasks", []),
                "total_estimated_hours": result.get("total_estimated_hours", 0)
            }
        
        except Exception as e:
            # Log error
            self.log_action("generate_tasks_error", "failed", error=str(e))
            
            return {
                "success": False,
                "error": str(e),
                "tasks": []
            }


# Global instance
task_generation_agent = TaskGenerationAgent()
