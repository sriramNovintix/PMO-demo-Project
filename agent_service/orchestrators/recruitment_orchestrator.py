"""
Recruitment Orchestrator
Handles candidate selection and promotion to employees
Uses: mongodb_tool, slack_tool
Sub-agents: resume_parser (external), candidate_selection
"""
from typing import Dict, Any, List
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import create_react_agent
from config import get_llm
from tools.mongodb_tool import mongodb_tool
from tools.slack_tool import slack_tool
from agents.base_agent import BaseAgent
from agentops.sdk.decorators import agent, workflow


@agent(name="recruitment_orchestrator")
class RecruitmentOrchestrator(BaseAgent):
    """
    Recruitment Orchestrator
    Coordinates candidate selection workflow
    """
    
    def __init__(self):
        super().__init__("recruitment_orchestrator")
        self.llm = get_llm()
        
        # Create react agent with tools
        self.agent = create_react_agent(
            self.llm,
            tools=[mongodb_tool, slack_tool],
            prompt="""You are the Recruitment Orchestrator.

Your responsibilities:
1. List available candidates
2. Select candidates and promote to employees
3. Reject candidates
4. Send notifications to Slack

Available Tools:
- mongodb_tool: Query/insert/delete candidates and employees
- slack_tool: Send notifications to Slack

When user wants to select a candidate:
1. Get candidates from MongoDB using mongodb_tool("find", "candidates")
2. Find the candidate by name
3. Create employee record using mongodb_tool("insert", "employees", data={...})
4. Delete candidate using mongodb_tool("delete", "candidates", query={"candidate_id": "..."})
5. Send welcome message to Slack

Always use tools to interact with database."""
        )
    
    @workflow(name="recruitment_workflow")
    def process(self, messages: List[BaseMessage], session_id: str) -> Dict[str, Any]:
        """
        Process recruitment request
        
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
recruitment_orchestrator = RecruitmentOrchestrator()
