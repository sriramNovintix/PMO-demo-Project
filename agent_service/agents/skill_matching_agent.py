"""
Skill Matching Agent
Matches employee skills to task requirements
Standalone runnable agent with state management
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, invoke_with_prompt
from agents.base_agent import BaseAgent
import json


class SkillMatchingAgent(BaseAgent):
    """
    Skill Matching Agent
    Analyzes employee skills and matches them to task requirements
    """
    
    def __init__(self):
        super().__init__("skill_matching_agent")
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Skill Matching Agent.
Your role is to match employee skills to task requirements.

For each task, analyze:
1. Which employees have the required skills
2. Skill match percentage for each employee
3. Workload balance considerations
4. Skill development opportunities

Respond in JSON format:
{{
    "task_matches": [
        {{
            "task_title": "Task name",
            "matches": [
                {{
                    "employee_name": "Name",
                    "match_score": 0.0-1.0,
                    "matching_skills": ["skill1"],
                    "missing_skills": ["skill2"],
                    "reasoning": "Why this match"
                }}
            ]
        }}
    ]
}}"""),
            ("human", """Tasks:
{tasks}

Employees:
{employees}

Match employees to tasks based on skills.""")
        ])
    
    def match_skills(self, tasks: List[Dict[str, Any]], employees: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Match employee skills to tasks
        
        Args:
            tasks: List of tasks with required skills
            employees: List of employees with their skills
        
        Returns:
            Skill matching results with state updates
        """
        try:
            # Log input
            self.log_action("match_skills_start", "processing", tasks_count=len(tasks), employees_count=len(employees))
            
            # Format tasks and employees for prompt
            tasks_str = json.dumps(tasks, indent=2)
            employees_str = json.dumps(employees, indent=2)
            
            response = invoke_with_prompt(
                self.prompt,
                self.llm,
                tasks=tasks_str,
                employees=employees_str
            )
            
            # Parse response
            content = response.content
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            
            # Log success
            self.log_action("match_skills_complete", "success", matches_count=len(result.get("task_matches", [])))
            
            return {
                "success": True,
                "task_matches": result.get("task_matches", [])
            }
        
        except Exception as e:
            # Log error
            self.log_action("match_skills_error", "failed", error=str(e))
            
            return {
                "success": False,
                "error": str(e),
                "task_matches": []
            }


# Global instance
skill_matching_agent = SkillMatchingAgent()
