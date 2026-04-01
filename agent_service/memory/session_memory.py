"""
Session Memory Manager with Database Persistence
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import db


class SessionMemory:
    """Session storage with database persistence"""
    
    def __init__(self):
        self.db = db
    
    def create_session(self, session_id: str) -> None:
        """Create new session in database"""
        self.db.create_session(session_id)
    
    def store_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """Store state for session in database"""
        self.db.store_session_state(session_id, state)
    
    def get_latest_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get latest state for session from database"""
        return self.db.get_session_state(session_id)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        return self.db.session_exists(session_id)
    
    def store_project(self, project_id: str, project_data: Dict[str, Any]) -> None:
        """Store project data in database"""
        self.db.store_project(project_id, project_data)
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project data from database"""
        return self.db.get_project(project_id)
    
    def get_all_employees(self) -> List[Dict[str, Any]]:
        """Get all employees from database"""
        return self.db.get_all_employees()
    
    def add_pending_approval(self, session_id: str, approval_data: Dict[str, Any]) -> None:
        """Add pending approval to database"""
        self.db.add_pending_approval(session_id, approval_data)
    
    def get_pending_approvals(self, session_id: str) -> List[Dict[str, Any]]:
        """Get pending approvals from database"""
        return self.db.get_pending_approvals(session_id)
    
    def clear_pending_approvals(self, session_id: str) -> None:
        """Clear pending approvals from database"""
        self.db.clear_pending_approvals(session_id)


# Global memory instance
memory = SessionMemory()
