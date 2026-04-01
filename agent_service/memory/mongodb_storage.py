"""
MongoDB Storage for Task Orchestrator
Stores projects, employees, and sessions in MongoDB
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pymongo import MongoClient
from config import Config


class MongoDBStorage:
    """MongoDB storage manager"""
    
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.MONGODB_DB_NAME]
        
        # Collections
        self.projects = self.db["projects"]
        self.employees = self.db["employees"]
        self.sessions = self.db["sessions"]
        self.candidates = self.db["candidates"]
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes"""
        self.projects.create_index("project_name", unique=True)
        self.employees.create_index("employee_name")
        self.sessions.create_index("session_id", unique=True)
        self.candidates.create_index("candidate_name")
    
    # ==================== Projects ====================
    
    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new project"""
        project_data["created_at"] = datetime.now().isoformat()
        project_data["updated_at"] = datetime.now().isoformat()
        
        result = self.projects.insert_one(project_data)
        project_data["_id"] = str(result.inserted_id)
        
        return project_data
    
    def get_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get project by name"""
        project = self.projects.find_one({"project_name": project_name})
        if project:
            project["_id"] = str(project["_id"])
        return project
    
    def update_project(self, project_name: str, updates: Dict[str, Any]) -> bool:
        """Update project"""
        updates["updated_at"] = datetime.now().isoformat()
        result = self.projects.update_one(
            {"project_name": project_name},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        projects = list(self.projects.find())
        for p in projects:
            p["_id"] = str(p["_id"])
        return projects
    
    # ==================== Employees ====================
    
    def add_employee(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add employee"""
        employee_data["created_at"] = datetime.now().isoformat()
        
        result = self.employees.insert_one(employee_data)
        employee_data["_id"] = str(result.inserted_id)
        
        return employee_data
    
    def get_employee(self, employee_name: str) -> Optional[Dict[str, Any]]:
        """Get employee by name"""
        employee = self.employees.find_one({"employee_name": employee_name})
        if employee:
            employee["_id"] = str(employee["_id"])
        return employee
    
    def list_employees(self) -> List[Dict[str, Any]]:
        """List all employees"""
        employees = list(self.employees.find())
        for e in employees:
            e["_id"] = str(e["_id"])
        return employees
    
    def update_employee(self, employee_name: str, updates: Dict[str, Any]) -> bool:
        """Update employee"""
        result = self.employees.update_one(
            {"employee_name": employee_name},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    # ==================== Candidates ====================
    
    def add_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add candidate"""
        candidate_data["created_at"] = datetime.now().isoformat()
        
        result = self.candidates.insert_one(candidate_data)
        candidate_data["_id"] = str(result.inserted_id)
        
        return candidate_data
    
    def get_candidate(self, candidate_name: str) -> Optional[Dict[str, Any]]:
        """Get candidate by name"""
        candidate = self.candidates.find_one({"candidate_name": candidate_name})
        if candidate:
            candidate["_id"] = str(candidate["_id"])
        return candidate
    
    def list_candidates(self) -> List[Dict[str, Any]]:
        """List all candidates"""
        candidates = list(self.candidates.find())
        for c in candidates:
            c["_id"] = str(c["_id"])
        return candidates
    
    # ==================== Sessions ====================
    
    def create_session(self, session_id: str) -> None:
        """Create new session"""
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "state_history": [],
            "current_project": None,
            "pending_approvals": []
        }
        
        self.sessions.insert_one(session_data)
    
    def store_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """Store state for session"""
        # Check if session exists
        session = self.sessions.find_one({"session_id": session_id})
        
        if not session:
            self.create_session(session_id)
        
        # Add state to history
        self.sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "state_history": {
                        "state": state,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            }
        )
    
    def get_latest_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get latest state for session"""
        session = self.sessions.find_one({"session_id": session_id})
        
        if session and session.get("state_history"):
            return session["state_history"][-1]["state"]
        
        return None
    
    def add_pending_approval(self, session_id: str, approval_data: Dict[str, Any]) -> None:
        """Add pending approval"""
        self.sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "pending_approvals": approval_data
                }
            }
        )
    
    def get_pending_approvals(self, session_id: str) -> List[Dict[str, Any]]:
        """Get pending approvals"""
        session = self.sessions.find_one({"session_id": session_id})
        
        if session:
            return session.get("pending_approvals", [])
        
        return []
    
    def clear_pending_approvals(self, session_id: str) -> None:
        """Clear pending approvals"""
        self.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"pending_approvals": []}}
        )


# Global instance
mongodb_storage = MongoDBStorage()
