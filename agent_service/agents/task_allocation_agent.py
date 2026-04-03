"""
Task Allocation Agent
Creates optimal task allocation plan based on skill matching
Standalone runnable agent with state management
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, invoke_with_prompt
from agents.base_agent import BaseAgent
from agentops.sdk.decorators import agent, operation
import json


@agent(name="task_allocation_agent")
class TaskAllocationAgent(BaseAgent):
    """
    Task Allocation Agent
    Creates balanced task allocation plan considering skills and workload
    """
    
    def __init__(self):
        super().__init__("task_allocation_agent")
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
            "tasks": [
                {{
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
    
    @operation(name="allocate_tasks")
    def allocate_tasks(self, skill_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create task allocation plan
        
        Args:
            skill_matches: Skill matching results from SkillMatchingAgent
        
        Returns:
            Task allocation plan with state updates
        """
        try:
            # Log input
            self.log_action("allocate_tasks_start", "processing", matches_count=len(skill_matches))
            
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
            
            # Log success
            self.log_action("allocate_tasks_complete", "success", assignments_count=len(result.get("assignments", {})))
            
            return {
                "success": True,
                "assignments": result.get("assignments", {}),
                "unassigned_tasks": result.get("unassigned_tasks", []),
                "allocation_reasoning": result.get("allocation_reasoning", "")
            }
        
        except Exception as e:
            # Log error
            self.log_action("allocate_tasks_error", "failed", error=str(e))
            
            return {
                "success": False,
                "error": str(e),
                "assignments": {}
            }


# Global instance
task_allocation_agent = TaskAllocationAgent()
