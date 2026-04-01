"""
Controller Agent - Non-deterministic decision maker
Analyzes user message and decides next steps dynamically
"""
from typing import Dict, Any, Optional
from config import get_llm
import json


class ControllerAgent:
    """
    Controller Agent - Master decision maker
    Analyzes user intent and determines workflow dynamically
    """
    
    def __init__(self):
        self.llm = get_llm()
    
    def _build_prompt(self, state: Dict[str, Any]) -> str:
        """Build prompt for controller agent"""
        completed = state.get("completed_agents", [])
        has_goal = bool(state.get("weekly_goal"))
        has_tasks = len(state.get("generated_tasks", [])) > 0
        has_project = bool(state.get("project_name"))
        user_msg_lower = state.get("user_message", "").lower()
        
        # Check if employees exist in database
        from database import db
        employees_in_db = db.get_all_employees()
        has_employees = len(employees_in_db) > 0
        
        return f"""You are a Controller Agent in a task orchestration system.
Your role is to analyze user messages and decide the next action dynamically.

CRITICAL RULES TO PREVENT LOOPS:
1. If weekly_goal EXISTS and tasks NOT generated yet → IMMEDIATELY run task_generation (don't ask for project name)
2. If goal_understanding already completed and goal exists → SKIP to task_generation
3. If task_generation already completed → move to next step (skill_matching or finalize)
4. NEVER ask for the same information twice
5. If user provides goal in message → extract it with goal_understanding, then IMMEDIATELY generate tasks
6. Use "Unnamed Project" if project_name missing - DON'T block on it
7. If user asks to "show tasks" or "display tasks" and tasks exist → run "none" to finalize and show them
8. If user mentions employee name and tasks exist → run skill_matching

Available workflows:
1. CREATE_PROJECT - User wants to create a new project
2. UPDATE_GOAL - User wants to update weekly goal
3. ADD_EMPLOYEE - User wants to add employee information
4. ASSIGN_TASKS - User wants to assign tasks to employees
5. MODIFY_ASSIGNMENT - User wants to modify existing assignments
6. STATUS_UPDATE - User wants to see status of tasks/employees
7. SEND_MESSAGE - User wants to send a message to Slack
8. SEND_STATUS - User wants to send status report to Slack

Available agents:
- goal_understanding: Extract project name and weekly goal from user message
- task_generation: Generate tasks from weekly goal (requires weekly_goal)
- skill_matching: Match tasks to employee skills (requires tasks + employees)
- task_allocation: Create allocation plan and execute assignments (requires skill matches)
- status: Show status updates
- message: Send Slack messages
- none: Finalize and end (use this to show tasks or complete workflow)

DECISION LOGIC (follow strictly):
1. User asks for status → run "status" agent
2. User wants to send message/update/task list to Slack → run "message" agent (will fetch from MongoDB)
3. User asks to "show tasks" or "display tasks" and tasks exist → run "none" to finalize
4. User provides goal but no weekly_goal in state → run "goal_understanding"
5. weekly_goal EXISTS and tasks NOT generated → run "task_generation" IMMEDIATELY
6. User mentions employee name (like "use sriram", "assign to john") BUT no employees in DB → run "none" with message asking to add employee via web interface
7. User asks to "assign tasks" or "assign to [name]" AND employees exist → run "skill_matching" (will auto-fetch employees from DB)
8. Tasks exist and employees exist → run "skill_matching"
9. Skill matches exist → run "task_allocation" (will execute assignments automatically)
10. Otherwise → run "none" to finalize

IMPORTANT: When user says "send task list" or "send to slack", ALWAYS run "message" agent.
The message agent will fetch ALL tasks from MongoDB (not session-specific) and send to Slack.

Respond in JSON format:
{{
    "workflow_type": "CREATE_PROJECT|UPDATE_GOAL|ADD_EMPLOYEE|ASSIGN_TASKS|MODIFY_ASSIGNMENT|STATUS_UPDATE|SEND_MESSAGE|SEND_STATUS",
    "next_agent": "goal_understanding|task_generation|skill_matching|task_allocation|status|message|none",
    "reasoning": "Why this decision",
    "missing_info": [],
    "response_to_user": "Message to show user (empty if continuing workflow)"
}}

User Message: {state.get("user_message", "")}

Current State:
- Project Name: {state.get("project_name") or "None"}
- Weekly Goal: {"EXISTS" if has_goal else "MISSING"}
- Generated Tasks: {len(state.get("generated_tasks", []))} tasks
- Employees in Database: {len(employees_in_db)} employees
- Completed Agents: {", ".join(completed) if completed else "None"}

Analysis:
- Has Goal: {has_goal}
- Has Tasks: {has_tasks}
- Has Project: {has_project}
- Has Employees: {has_employees}
- Goal Understanding Done: {"goal_understanding" in completed}
- Task Generation Done: {"task_generation" in completed}
- User asking to show tasks: {"show" in user_msg_lower and "task" in user_msg_lower}
- User mentions employee: {"sriram" in user_msg_lower or "assign" in user_msg_lower or "use" in user_msg_lower}

What should happen next?"""
    
    def decide_next_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze state and decide next action
        
        Args:
            state: Current agent state
        
        Returns:
            Decision with next_agent, workflow_type, and reasoning
        """
        try:
            # Build prompt
            prompt = self._build_prompt(state)
            
            # Call LLM
            response = self.llm.invoke(prompt)
            
            # Parse LLM response
            content = response.content
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Find JSON object
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                content = content[start:end+1]
            
            decision = json.loads(content)
            
            return {
                "success": True,
                "workflow_type": decision.get("workflow_type"),
                "next_agent": decision.get("next_agent"),
                "reasoning": decision.get("reasoning"),
                "missing_info": decision.get("missing_info", []),
                "response_to_user": decision.get("response_to_user", "")
            }
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Controller Agent Error: {str(e)}")
            print(f"Traceback: {error_trace}")
            
            return {
                "success": False,
                "error": str(e),
                "next_agent": "none",
                "response_to_user": f"Error analyzing request: {str(e)}"
            }


# Global instance
controller_agent = ControllerAgent()
