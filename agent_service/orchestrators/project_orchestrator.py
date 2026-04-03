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
            prompt="""You are the Project Orchestrator.

Your responsibilities:
1. Understand project goals (extract project name and weekly goal)
2. Generate tasks from goals
3. Match employee skills to tasks
4. Allocate tasks to employees
5. Store everything in MongoDB
6. Send notifications to Slack

Available Tools:
- mongodb_tool: Query/insert/update database (employees, tasks, sessions)
- slack_tool: Send messages to Slack channels

When user provides a goal:
1. Extract project name and goal
2. Generate 5-10 actionable tasks
3. Get employees from MongoDB
4. Match skills and allocate tasks
5. Update MongoDB with assignments
6. Send summary to Slack

Always use tools to get data and update state."""
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
