"""
Skill Matching Agent
Matches employee skills to task requirements - Autonomous agent
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, invoke_with_prompt


class SkillMatchingAgent:
    """
    Skill Matching Agent - Autonomous
    Fetches its own data and matches employee skills to task requirements
    """
    
    def __init__(self):
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
            "task_id": "task_id",
            "matches": [
                {{
                    "employee_name": "Name",
                    "employee_id": "id",
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
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute skill matching - autonomous method
        Fetches data, processes, and returns results
        
        Args:
            state: Current state (may contain tasks, employees, session_id)
        
        Returns:
            Result with task_matches and updated state
        """
        try:
            # Get tasks - from state or database
            tasks = state.get("generated_tasks", [])
            if not tasks:
                # Fetch from database
                from database import db
                session_id = state.get("session_id")
                if session_id:
                    tasks = db.get_all_tasks(session_id)
            
            if not tasks:
                return {
                    "success": False,
                    "error": "No tasks available for matching",
                    "task_matches": [],
                    "state_updates": {}
                }
            
            # Get employees - from state or database
            employees = state.get("employees", [])
            if not employees:
                # Fetch from database
                from database import db
                employees = db.get_all_employees()
            
            if not employees:
                return {
                    "success": False,
                    "error": "No employees found in database",
                    "task_matches": [],
                    "state_updates": {},
                    "message": "Please add employees to the system first."
                }
            
            # Perform skill matching
            result = self.match_skills(tasks, employees)
            
            if result["success"]:
                return {
                    "success": True,
                    "task_matches": result["task_matches"],
                    "state_updates": {
                        "skill_matches": result["task_matches"],
                        "employees": employees,
                        "generated_tasks": tasks
                    },
                    "message": f"Matched {len(result['task_matches'])} tasks to employees"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error"),
                    "task_matches": [],
                    "state_updates": {}
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task_matches": [],
                "state_updates": {}
            }
    
    def match_skills(self, tasks: List[Dict[str, Any]], employees: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Match employee skills to tasks
        
        Args:
            tasks: List of tasks with required skills
            employees: List of employees with their skills
        
        Returns:
            Skill matching results
        """
        try:
            import json
            
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
            
            return {
                "success": True,
                "task_matches": result.get("task_matches", [])
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task_matches": []
            }


# Global instance
skill_matching_agent = SkillMatchingAgent()
