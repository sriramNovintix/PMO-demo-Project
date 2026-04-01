"""
Task Generation Agent
Generates actionable tasks from weekly goals
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, invoke_with_prompt


class TaskGenerationAgent:
    """
    Task Generation Agent
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
