"""
State Management for Task Orchestrator
Tracks conversation state and workflow progress
"""
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
from enum import Enum


class WorkflowType(str, Enum):
    """Types of workflows"""
    CREATE_PROJECT = "create_project"
    UPDATE_GOAL = "update_goal"
    ADD_EMPLOYEE = "add_employee"
    ASSIGN_TASKS = "assign_tasks"
    MODIFY_ASSIGNMENT = "modify_assignment"


class AgentState(TypedDict):
    """State that flows through the orchestrator"""
    # Session info
    session_id: str
    user_message: str
    workflow_type: Optional[WorkflowType]
    
    # Project context
    project_name: Optional[str]
    project_id: Optional[str]
    slack_channel_id: Optional[str]
    trello_board_id: Optional[str]
    
    # Goal and tasks
    weekly_goal: Optional[str]
    generated_tasks: List[Dict[str, Any]]
    
    # Employee context
    employees: List[Dict[str, Any]]
    employee_skills: Dict[str, List[str]]
    
    # Task assignment
    assignment_plan: Optional[Dict[str, Any]]
    pending_approval: bool
    approved: bool
    
    # Agent decisions
    next_agent: Optional[str]
    completed_agents: List[str]
    
    # Messages and responses
    agent_messages: List[Dict[str, Any]]
    response_to_user: str
    
    # Conversation history (for context window)
    conversation_history: List[Dict[str, Any]]
    
    # Metadata
    created_at: str
    last_updated: str


def create_initial_state(session_id: str, user_message: str) -> AgentState:
    """Create initial agent state"""
    return AgentState(
        session_id=session_id,
        user_message=user_message,
        workflow_type=None,
        project_name=None,
        project_id=None,
        slack_channel_id=None,
        trello_board_id=None,
        weekly_goal=None,
        generated_tasks=[],
        employees=[],
        employee_skills={},
        assignment_plan=None,
        pending_approval=False,
        approved=False,
        next_agent=None,
        completed_agents=[],
        agent_messages=[],
        response_to_user="",
        conversation_history=[],
        created_at=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat()
    )


def add_agent_message(state: AgentState, from_agent: str, to_agent: str, message: str, data: Optional[Dict] = None):
    """Add message between agents"""
    state["agent_messages"].append({
        "from": from_agent,
        "to": to_agent,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    })
    state["last_updated"] = datetime.now().isoformat()


def mark_agent_completed(state: AgentState, agent_name: str):
    """Mark agent as completed"""
    if agent_name not in state["completed_agents"]:
        state["completed_agents"].append(agent_name)
    state["last_updated"] = datetime.now().isoformat()


def add_to_conversation_history(
    state: AgentState,
    role: str,
    content: str,
    data: Optional[Dict] = None,
    max_history: int = 20
):
    """
    Add message to conversation history with context window management
    
    Args:
        state: Agent state
        role: 'user' or 'agent'
        content: Message content
        data: Optional additional data
        max_history: Maximum number of messages to keep (default 20 = 10 exchanges)
    """
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    # Add to history
    if "conversation_history" not in state:
        state["conversation_history"] = []
    
    state["conversation_history"].append(message)
    
    # Trim history if exceeds max_history
    # Keep the most recent messages within the context window
    if len(state["conversation_history"]) > max_history:
        # Keep first message (welcome/context) and recent messages
        state["conversation_history"] = (
            state["conversation_history"][:1] +  # Keep first message
            state["conversation_history"][-(max_history-1):]  # Keep recent messages
        )
    
    state["last_updated"] = datetime.now().isoformat()


def get_conversation_context(state: AgentState, last_n: int = 5) -> str:
    """
    Get recent conversation context as a formatted string
    
    Args:
        state: Agent state
        last_n: Number of recent exchanges to include
    
    Returns:
        Formatted conversation context
    """
    if "conversation_history" not in state or not state["conversation_history"]:
        return "No previous conversation"
    
    # Get last N messages
    recent_messages = state["conversation_history"][-last_n*2:]  # last_n exchanges (user + agent)
    
    context_lines = []
    for msg in recent_messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        # Truncate long messages
        if len(content) > 200:
            content = content[:200] + "..."
        context_lines.append(f"{role.upper()}: {content}")
    
    return "\n".join(context_lines)
