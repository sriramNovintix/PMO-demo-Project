"""
Central Orchestrator
Analyzes user intent and delegates to appropriate sub-orchestrators
Supervisor pattern with intelligent routing
"""
from typing import Dict, Any, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from config import get_llm
from orchestrators.project_orchestrator import project_orchestrator
from orchestrators.recruitment_orchestrator import recruitment_orchestrator
from orchestrators.communication_orchestrator import communication_orchestrator
from memory.session_memory import memory
import datetime


class AgentState(TypedDict):
    """State for central orchestrator"""
    messages: Sequence[BaseMessage]
    session_id: str
    next: str


class CentralOrchestrator:
    """
    Central Orchestrator
    Analyzes intent and routes to sub-orchestrators
    """
    
    def __init__(self):
        self.llm = get_llm()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build LangGraph workflow"""
        
        # Supervisor prompt
        supervisor_prompt = """You are a supervisor managing three sub-orchestrators:
- 'project': Handles goals, task generation, skill matching, task allocation
- 'recruitment': Handles candidate selection and promotion to employees
- 'communication': Handles Slack messages and status updates

Analyze the user request and decide which orchestrator should handle it:
- Use 'project' if user talks about goals, tasks, assignments, or project management
- Use 'recruitment' if user talks about selecting candidates or hiring
- Use 'communication' if user explicitly says "send to slack", "send slack", "notify slack"
- Use 'finish' if the request has been completed

Respond with ONLY the orchestrator name in lowercase ('project', 'recruitment', 'communication') or 'finish'."""
        
        def supervisor_node(state: AgentState) -> dict:
            """Supervisor decides which orchestrator to use"""
            # If last message is from AI, we're done
            if state["messages"] and state["messages"][-1].type == "ai":
                return {"next": "finish"}
            
            messages = [SystemMessage(content=supervisor_prompt)] + list(state["messages"])
            response = self.llm.invoke(messages)
            decision = response.content.strip().lower()
            
            valid_next = ["project", "recruitment", "communication", "finish"]
            if decision not in valid_next:
                # Fallback logic
                msg_text = state["messages"][-1].content.lower()
                if any(phrase in msg_text for phrase in ["send to slack", "send slack", "notify slack"]):
                    decision = "communication"
                elif any(word in msg_text for word in ["select", "candidate", "hire"]):
                    decision = "recruitment"
                else:
                    decision = "project"
            
            return {"next": decision}
        
        def project_node(state: AgentState):
            """Project orchestrator node"""
            result = project_orchestrator.process(state["messages"], state["session_id"])
            return {"messages": result["messages"]}
        
        def recruitment_node(state: AgentState):
            """Recruitment orchestrator node"""
            result = recruitment_orchestrator.process(state["messages"], state["session_id"])
            return {"messages": result["messages"]}
        
        def communication_node(state: AgentState):
            """Communication orchestrator node"""
            result = communication_orchestrator.process(state["messages"], state["session_id"])
            return {"messages": result["messages"]}
        
        # Build graph
        workflow = StateGraph(AgentState)
        workflow.add_node("supervisor", supervisor_node)
        workflow.add_node("project", project_node)
        workflow.add_node("recruitment", recruitment_node)
        workflow.add_node("communication", communication_node)
        
        # Routing
        workflow.add_edge(START, "supervisor")
        workflow.add_conditional_edges(
            "supervisor",
            lambda state: state["next"].lower(),
            {
                "project": "project",
                "recruitment": "recruitment",
                "communication": "communication",
                "finish": END
            }
        )
        
        # Route back to supervisor after orchestrators complete
        workflow.add_edge("project", "supervisor")
        workflow.add_edge("recruitment", "supervisor")
        workflow.add_edge("communication", "supervisor")
        
        return workflow.compile()
    
    def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process user message through orchestrators
        
        Args:
            session_id: Session identifier
            user_message: User's message
        
        Returns:
            Processing result
        """
        try:
            # Load session memory
            existing_state = memory.get_latest_state(session_id)
            if not existing_state:
                memory.create_session(session_id)
                existing_state = {
                    "conversation_history": [],
                    "agent_messages": []
                }
            
            # Reconstruct message history
            history_msgs = []
            for msg_data in existing_state.get("conversation_history", []):
                role = msg_data.get("role")
                content = msg_data.get("content", "")
                if role == "user":
                    history_msgs.append(HumanMessage(content=content))
                elif role == "agent":
                    history_msgs.append(AIMessage(content=content))
            
            # Add current message
            current_message = HumanMessage(content=f"[Session: {session_id}] {user_message}")
            history_msgs.append(current_message)
            
            # Save user message
            existing_state.setdefault("conversation_history", []).append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Invoke graph
            initial_state = {
                "messages": history_msgs,
                "session_id": session_id,
                "next": ""
            }
            config = {"recursion_limit": 15}
            
            try:
                final_state = self.graph.invoke(initial_state, config=config)
            except KeyError as e:
                # Handle routing errors
                if "FINISH" in str(e) or "finish" in str(e):
                    # Fallback: use project orchestrator directly
                    from orchestrators.project_orchestrator import project_orchestrator
                    result = project_orchestrator.process(history_msgs, session_id)
                    final_state = {"messages": result["messages"]}
                else:
                    raise
            
            # Extract final response
            final_messages = final_state.get("messages", [])
            response_text = "Task completed."
            for msg in reversed(final_messages):
                if msg.type == "ai" and msg.content:
                    response_text = msg.content
                    break
            
            # Save agent response
            existing_state["conversation_history"].append({
                "role": "agent",
                "content": response_text,
                "timestamp": datetime.datetime.now().isoformat()
            })
            memory.store_state(session_id, existing_state)
            
            return {
                "success": True,
                "session_id": session_id,
                "response": response_text
            }
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in central orchestrator: {error_trace}")
            return {
                "success": False,
                "session_id": session_id,
                "response": f"Error: {str(e)}",
                "traceback": error_trace
            }


# Global instance
central_orchestrator = CentralOrchestrator()
