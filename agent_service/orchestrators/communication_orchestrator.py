"""
Communication Orchestrator
Handles Slack notifications and messages
Uses: mongodb_tool, slack_tool
Sub-agents: status_agent, message_formatter
"""
from typing import Dict, Any, List
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import create_react_agent
from config import get_llm
from tools.mongodb_tool import mongodb_tool
from tools.slack_tool import slack_tool
from agents.base_agent import BaseAgent


class CommunicationOrchestrator(BaseAgent):
    """
    Communication Orchestrator
    Coordinates Slack communication workflow
    """
    
    def __init__(self):
        super().__init__("communication_orchestrator")
        self.llm = get_llm()
        
        # Create react agent with tools
        self.agent = create_react_agent(
            self.llm,
            tools=[mongodb_tool, slack_tool],
            prompt="""You are the Communication Orchestrator.

Your responsibilities:
1. Send status updates to Slack
2. Send custom messages to Slack
3. Format messages professionally
4. Get data from MongoDB for status updates

Available Tools:
- mongodb_tool: Query database for status information
- slack_tool: Send messages to Slack channels

When user wants to send status to Slack:
1. Get employee status from MongoDB
2. Get tasks from MongoDB
3. Format a nice status message
4. Send to Slack using slack_tool("send_message", "demo-projects", message)

When user wants to send custom message:
1. Extract the message content
2. Send to Slack using slack_tool("send_message", "demo-projects", message)

Always use tools to get data and send messages."""
        )
    
    def process(self, messages: List[BaseMessage], session_id: str) -> Dict[str, Any]:
        """
        Process communication request
        
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
communication_orchestrator = CommunicationOrchestrator()
