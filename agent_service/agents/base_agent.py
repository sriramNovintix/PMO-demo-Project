"""
Base Agent - Common functionality for all agents
"""
from typing import Dict, Any, List
from datetime import datetime


class AgentState:
    """Base state class for agents"""
    
    def __init__(self):
        self.actions = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def add_action(self, action: Dict[str, Any]):
        """Add action to state history"""
        action["timestamp"] = datetime.now().isoformat()
        self.actions.append(action)
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            "actions": self.actions,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """Create state from dictionary"""
        state = cls()
        state.actions = data.get("actions", [])
        state.created_at = data.get("created_at", datetime.now().isoformat())
        state.updated_at = data.get("updated_at", datetime.now().isoformat())
        return state


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.state = AgentState()
    
    def get_state(self) -> Dict[str, Any]:
        """Get agent state"""
        return {
            "agent_name": self.name,
            **self.state.to_dict()
        }
    
    def load_state(self, state_data: Dict[str, Any]) -> None:
        """Load agent state"""
        self.state = AgentState.from_dict(state_data)
    
    def log_action(self, action_type: str, result: str, **kwargs):
        """Log action to state"""
        self.state.add_action({
            "action_type": action_type,
            "result": result,
            **kwargs
        })
