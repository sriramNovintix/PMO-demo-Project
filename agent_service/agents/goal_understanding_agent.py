"""
Goal Understanding Agent
Extracts and clarifies project goals from user input
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, invoke_with_prompt
try:
    from agentops.sdk.decorators import agent, operation
    AGENTOPS_AVAILABLE = True
except ImportError:
    AGENTOPS_AVAILABLE = False
    # Create dummy decorators if agentops not available
    def agent(cls):
        return cls
    def operation(func):
        return func


class GoalUnderstandingAgent:
    """
    Goal Understanding Agent - Autonomous
    Extracts project name, weekly goal, and clarifies requirements
    """
    
    
    def __init__(self):
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Goal Understanding Agent.
Your role is to extract and clarify project goals from user messages.

Extract:
1. Project name
2. Weekly goal description
3. Key deliverables
4. Success criteria

If information is unclear, identify what needs clarification.

Respond in JSON format:
{{
    "project_name": "extracted project name",
    "weekly_goal": "clear goal description",
    "key_deliverables": ["deliverable1", "deliverable2"],
    "success_criteria": ["criteria1", "criteria2"],
    "needs_clarification": ["what needs clarification"],
    "confidence": 0.0-1.0
}}"""),
            ("human", """User Message: {user_message}

Current Context:
- Project Name: {project_name}
- Existing Goal: {existing_goal}

Extract and clarify the goal.""")
        ])
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute goal understanding - autonomous method
        Extracts project name and weekly goal from user message
        
        Args:
            state: Current state with user_message
        
        Returns:
            Result with extracted goal information and state updates
        """
        try:
            user_message = state.get("user_message", "")
            if not user_message:
                return {
                    "success": False,
                    "error": "No user message provided",
                    "state_updates": {},
                    "message": "Please provide a message"
                }
            
            existing_context = {
                "project_name": state.get("project_name"),
                "weekly_goal": state.get("weekly_goal")
            }
            
            result = self.understand_goal(user_message, existing_context)
            
            if result["success"]:
                # Extract project name and goal
                extracted_project = result.get("project_name")
                extracted_goal = result.get("weekly_goal")
                
                state_updates = {}
                
                # Only update if we got new information
                if extracted_project and extracted_project != "None" and extracted_project.lower() != "none":
                    state_updates["project_name"] = extracted_project
                
                if extracted_goal and extracted_goal != "None" and extracted_goal.lower() != "none":
                    state_updates["weekly_goal"] = extracted_goal
                
                return {
                    "success": True,
                    "state_updates": state_updates,
                    "extracted_data": result,
                    "message": "Goal extracted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error"),
                    "state_updates": {},
                    "message": f"Failed to extract goal: {result.get('error')}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "state_updates": {},
                "message": f"Error: {str(e)}"
            }
    
    @operation
    def understand_goal(self, user_message: str, existing_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract and understand project goal
        
        Args:
            user_message: User's message
            existing_context: Existing project context
        
        Returns:
            Extracted goal information
        """
        try:
            existing_context = existing_context or {}
            
            # Format and invoke
            response = invoke_with_prompt(
                self.prompt,
                self.llm,
                user_message=user_message,
                project_name=existing_context.get("project_name") or "None",
                existing_goal=existing_context.get("weekly_goal") or "None"
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
                **result
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
goal_understanding_agent = GoalUnderstandingAgent()
