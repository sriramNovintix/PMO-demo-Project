"""
Task Allocation Agent
Creates optimal task allocation plan - Autonomous agent
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, invoke_with_prompt


class TaskAllocationAgent:
    """
    Task Allocation Agent - Autonomous
    Creates balanced task allocation plan and executes assignments
    """
    
    def __init__(self):
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Task Allocation Agent.
Your role is to create an optimal task allocation plan.

Consider:
1. Skill match scores
2. Workload balance (distribute hours evenly)
3. Task priorities
4. Employee capacity
5. Skill development opportunities

Create a balanced allocation where each employee gets appropriate tasks.

Respond in JSON format:
{{
    "assignments": {{
        "Employee Name": {{
            "employee_id": "id",
            "tasks": [
                {{
                    "task_id": "id",
                    "title": "Task title",
                    "estimated_hours": 8,
                    "match_score": 0.9,
                    "reasoning": "Why assigned"
                }}
            ],
            "total_hours": 16,
            "workload_percentage": 40
        }}
    }},
    "unassigned_tasks": [],
    "allocation_reasoning": "Overall allocation strategy"
}}"""),
            ("human", """Skill Matching Results:
{skill_matches}

Employee Capacity: 40 hours/week per employee

Create optimal allocation plan.""")
        ])
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task allocation - autonomous method
        Creates allocation plan and saves to database
        
        Args:
            state: Current state with skill_matches
        
        Returns:
            Result with assignment_plan and updated state
        """
        try:
            # Get skill matches from state
            skill_matches = state.get("skill_matches", [])
            if not skill_matches:
                return {
                    "success": False,
                    "error": "No skill matching results available",
                    "assignment_plan": {},
                    "state_updates": {},
                    "message": "Please run skill matching first"
                }
            
            # Create allocation plan
            result = self.allocate_tasks(skill_matches)
            
            if not result["success"]:
                return {
                    "success": False,
                    "error": result.get("error"),
                    "assignment_plan": {},
                    "state_updates": {}
                }
            
            # Execute assignments - save to database and send notifications
            execution_result = self._execute_assignments(
                result,
                state.get("session_id"),
                state.get("project_name")
            )
            
            return {
                "success": True,
                "assignment_plan": result,
                "execution_result": execution_result,
                "state_updates": {
                    "assignment_plan": result
                },
                "message": execution_result.get("message", "Tasks allocated successfully")
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "assignment_plan": {},
                "state_updates": {}
            }
    
    def _execute_assignments(self, assignment_plan: Dict[str, Any], session_id: str, project_id: str) -> Dict[str, Any]:
        """Execute assignments - save to DB and send Slack notifications"""
        try:
            from database import db
            from tools.slack_tools import slack_tools
            
            assignments = assignment_plan.get("assignments", {})
            employees_data = db.get_all_employees()
            
            # Update tasks in database
            for employee_name, employee_data in assignments.items():
                employee_email = next((e["email"] for e in employees_data if e["name"] == employee_name), None)
                tasks = employee_data.get("tasks", [])
                
                for task in tasks:
                    if task.get("task_id"):
                        # Update task with assignment
                        db.tasks.update_one(
                            {"task_id": task["task_id"]},
                            {"$set": {
                                "assigned_to": employee_name,
                                "assigned_to_email": employee_email,
                                "updated_at": __import__('datetime').datetime.now().isoformat()
                            }}
                        )
                
                # Send Slack notification
                message = f"📋 *New Task Assignment*\n\n"
                message += f"*{employee_name}* ({employee_email})\n"
                message += f"Total: {len(tasks)} tasks ({employee_data.get('total_hours', 0)}h)\n\n"
                for i, task in enumerate(tasks, 1):
                    message += f"{i}. {task.get('title')} ({task.get('estimated_hours')}h)\n"
                
                slack_tools.send_message_to_channel("demo-projects", message)
            
            return {
                "success": True,
                "message": f"✅ Tasks assigned to {len(assignments)} employees"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"⚠️ Assignment execution failed: {str(e)}"
            }
    
    def allocate_tasks(self, skill_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create task allocation plan
        
        Args:
            skill_matches: Skill matching results from SkillMatchingAgent
        
        Returns:
            Task allocation plan
        """
        try:
            import json
            
            skill_matches_str = json.dumps(skill_matches, indent=2)
            
            response = invoke_with_prompt(
                self.prompt,
                self.llm,
                skill_matches=skill_matches_str
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
                "assignments": result.get("assignments", {}),
                "unassigned_tasks": result.get("unassigned_tasks", []),
                "allocation_reasoning": result.get("allocation_reasoning", "")
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "assignments": {}
            }


# Global instance
task_allocation_agent = TaskAllocationAgent()
