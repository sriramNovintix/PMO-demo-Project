"""
Project Orchestrator
Handles project management: goal understanding, task generation, skill matching, task allocation
Uses: mongodb_tool, slack_tool
Sub-agents: goal_understanding, task_generation, skill_matching, task_allocation
"""
from typing import Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from config import get_llm
from tools.mongodb_tool import mongodb_tool
from tools.slack_tool import slack_tool
from agents.base_agent import BaseAgent
from agentops.sdk.decorators import agent, workflow


@agent(name="project_orchestrator")
class ProjectOrchestrator(BaseAgent):
    """
    Project Orchestrator
    Coordinates project management workflow
    """
    
    def __init__(self):
        super().__init__("project_orchestrator")
        self.llm = get_llm()
        
        # Create react agent with tools
        self.agent = create_react_agent(
            self.llm,
            tools=[mongodb_tool, slack_tool],
            prompt="""You are the Project Orchestrator - a smart task management assistant.

Your responsibilities:
1. Understand project goals and generate tasks
2. Assign tasks to employees by NAME (no email needed)
3. Create new tasks when requested
4. Handle reassignments directly without asking questions

IMPORTANT RULES:
- When user says "assign task X to Y" → Find employee by name (case-insensitive), assign directly
- When user says "create task X and assign to Y" → Create task, then assign to employee by name
- When user says "reassign task X to Y" → Update assignment directly, no questions
- Employee names are enough - NO need to ask for email addresses
- If employee name not found, list available employees and ask which one
- Be direct and efficient - minimize questions

Available Tools:
- mongodb_tool: Query/insert/update database
  - get_employees: Get all employees (returns name, skills, capacity)
  - get_tasks: Get all tasks
  - update_task: Update task assignment (use employee NAME, not email)
  - create_task: Create new task
- slack_tool: Send notifications

Workflow Examples:

1. "assign task_123 to sriram"
   → get_employees → find "sriram" → update_task with name → send slack notification

2. "create data pipeline task and assign to varun"
   → create_task → get_employees → find "varun" → update_task → send slack

3. "reassign task_456 to sathya"
   → get_employees → find "sathya" → update_task → send slack

Always use employee NAME for assignments, not email."""
        )
    
    @workflow(name="project_workflow")
    def process(self, messages: List[BaseMessage], session_id: str) -> Dict[str, Any]:
        """
        Process project management request
        
        Args:
            messages: Conversation messages
            session_id: Session identifier
        
        Returns:
            Result with updated messages
        """
        try:
            self.log_action("process_start", "processing", session_id=session_id)
            
            # Invoke agent
            result = self.agent.invoke({"messages": messages})
            
            self.log_action("process_complete", "success", session_id=session_id)
            
            return result
        
        except Exception as e:
            self.log_action("process_error", "failed", session_id=session_id, error=str(e))
            raise


# Global instance
project_orchestrator = ProjectOrchestrator()
