"""
Database Layer - MongoDB for persistence
Stores sessions, projects, employees, and candidates
"""
from pymongo import MongoClient
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
import json


class Database:
    """MongoDB database for persistent storage"""
    
    def __init__(self, mongodb_uri: str, db_name: str):
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        
        # Collections
        self.sessions = self.db["sessions"]
        self.projects = self.db["projects"]
        self.candidates = self.db["candidates"]
        self.employees = self.db["employees"]
        self.tasks = self.db["tasks"]
        self.pending_approvals = self.db["pending_approvals"]
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes"""
        self.sessions.create_index("session_id", unique=True)
        self.candidates.create_index("email")
        self.employees.create_index("email")
        self.tasks.create_index("task_id", unique=True)
        self.tasks.create_index("assigned_to")
        self.tasks.create_index("status")
    
    # Session operations
    def create_session(self, session_id: str) -> None:
        """Create new session"""
        now = datetime.now().isoformat()
        
        self.sessions.update_one(
            {"session_id": session_id},
            {
                "$setOnInsert": {
                    "session_id": session_id,
                    "created_at": now,
                    "last_updated": now,
                    "state_data": {}
                }
            },
            upsert=True
        )
    
    def store_session_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """Store session state"""
        now = datetime.now().isoformat()
        
        self.sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "state_data": state,
                    "last_updated": now
                }
            },
            upsert=True
        )
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session state"""
        session = self.sessions.find_one({"session_id": session_id})
        if session:
            return session.get("state_data")
        return None
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all sessions"""
        sessions = list(self.sessions.find().sort("last_updated", -1))
        result = []
        for session in sessions:
            state_data = session.get("state_data", {})
            result.append({
                "session_id": session["session_id"],
                "project_name": state_data.get("project_name"),
                "weekly_goal": state_data.get("weekly_goal"),
                "created_at": session.get("created_at", ""),
                "last_updated": session.get("last_updated", "")
            })
        return result
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        return self.sessions.find_one({"session_id": session_id}) is not None
    
    # Project operations
    def store_project(self, project_id: str, project_data: Dict[str, Any]) -> None:
        """Store project"""
        now = datetime.now().isoformat()
        
        self.projects.update_one(
            {"project_id": project_id},
            {
                "$set": {
                    **project_data,
                    "project_id": project_id,
                    "updated_at": now
                },
                "$setOnInsert": {
                    "created_at": project_data.get("created_at", now)
                }
            },
            upsert=True
        )
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project"""
        project = self.projects.find_one({"project_id": project_id})
        if project:
            project.pop("_id", None)
            return project
        return None
    
    # Candidate operations
    def add_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add candidate from parsed resume"""
        now = datetime.now().isoformat()
        
        # Generate ID
        name_part = candidate_data["name"].lower().replace(" ", "_")
        timestamp_part = now.replace(":", "").replace("-", "").replace(".", "")[:14]
        candidate_id = f"cand_{name_part}_{timestamp_part}"
        
        try:
            doc = {
                "candidate_id": candidate_id,
                "name": candidate_data["name"],
                "email": candidate_data.get("email"),
                "resume_data": candidate_data.get("resume_data", {}),
                "skills": candidate_data.get("skills", []),
                "experience_years": candidate_data.get("experience_years", 0),
                "status": "pending",
                "created_at": now,
                "updated_at": now
            }
            
            self.candidates.insert_one(doc)
            
            return {
                "success": True,
                "candidate_id": candidate_id,
                "message": "Candidate added successfully"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_all_candidates(self) -> List[Dict[str, Any]]:
        """Get all candidates"""
        candidates = list(self.candidates.find().sort("created_at", -1))
        for candidate in candidates:
            candidate.pop("_id", None)
        return candidates
    
    def select_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Select candidate - move to employees"""
        candidate = self.candidates.find_one({"candidate_id": candidate_id})
        
        if not candidate:
            return {"success": False, "error": "Candidate not found"}
        
        # Create employee from candidate
        now = datetime.now().isoformat()
        name_part = candidate["name"].lower().replace(" ", "_")
        employee_id = f"emp_{name_part}_{now.replace(':', '').replace('-', '').replace('.', '')[:14]}"
        
        try:
            employee_doc = {
                "employee_id": employee_id,
                "name": candidate["name"],
                "email": candidate.get("email"),
                "skills": candidate.get("skills", []),
                "experience_years": candidate.get("experience_years", 0),
                "current_tasks": [],
                "created_at": now,
                "updated_at": now
            }
            
            self.employees.insert_one(employee_doc)
            
            # Delete candidate
            self.candidates.delete_one({"candidate_id": candidate_id})
            
            return {
                "success": True,
                "employee_id": employee_id,
                "message": "Candidate selected and moved to employees"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def reject_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Reject candidate - delete from database"""
        result = self.candidates.delete_one({"candidate_id": candidate_id})
        
        if result.deleted_count > 0:
            return {
                "success": True,
                "message": "Candidate rejected and deleted"
            }
        else:
            return {
                "success": False,
                "error": "Candidate not found"
            }
    
    # Employee operations
    def add_employee(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add employee directly"""
        now = datetime.now().isoformat()
        name_part = employee_data["name"].lower().replace(" ", "_")
        employee_id = f"emp_{name_part}_{now.replace(':', '').replace('-', '').replace('.', '')[:14]}"
        
        try:
            doc = {
                "employee_id": employee_id,
                "name": employee_data["name"],
                "email": employee_data.get("email"),
                "skills": employee_data.get("skills", []),
                "experience_years": employee_data.get("experience_years", 0),
                "current_tasks": [],
                "created_at": now,
                "updated_at": now
            }
            
            self.employees.insert_one(doc)
            
            return {
                "success": True,
                "employee_id": employee_id,
                "message": "Employee added successfully"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_all_employees(self) -> List[Dict[str, Any]]:
        """Get all employees"""
        employees = list(self.employees.find().sort("created_at", -1))
        for employee in employees:
            employee.pop("_id", None)
        return employees
    
    def update_employee_tasks(self, employee_id: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update employee's current tasks"""
        result = self.employees.update_one(
            {"employee_id": employee_id},
            {
                "$set": {
                    "current_tasks": tasks,
                    "updated_at": datetime.now().isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Tasks updated"}
        else:
            return {"success": False, "error": "Employee not found"}
    
    def delete_employee(self, employee_id: str) -> Dict[str, Any]:
        """Delete employee"""
        result = self.employees.delete_one({"employee_id": employee_id})
        
        if result.deleted_count > 0:
            return {
                "success": True,
                "message": "Employee deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": "Employee not found"
            }
    
    # Task operations
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task"""
        now = datetime.now().isoformat()
        
        # Generate task ID
        title_part = task_data["title"][:20].lower().replace(" ", "_")
        timestamp_part = now.replace(":", "").replace("-", "").replace(".", "")[:14]
        task_id = f"task_{title_part}_{timestamp_part}"
        
        try:
            doc = {
                "task_id": task_id,
                "title": task_data["title"],
                "description": task_data.get("description", ""),
                "assigned_to": task_data.get("assigned_to"),
                "assigned_to_email": task_data.get("assigned_to_email"),
                "estimated_hours": task_data.get("estimated_hours", 0),
                "status": "todo",  # todo, in_progress, completed
                "project_id": task_data.get("project_id"),
                "session_id": task_data.get("session_id"),
                "created_at": now,
                "updated_at": now,
                "completed_at": None
            }
            
            self.tasks.insert_one(doc)
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task created successfully"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_all_tasks(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tasks, optionally filtered by session"""
        query = {"session_id": session_id} if session_id else {}
        tasks = list(self.tasks.find(query).sort("created_at", -1))
        for task in tasks:
            task.pop("_id", None)
        return tasks
    
    def get_tasks_by_status(self, status: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks by status"""
        query = {"status": status}
        if session_id:
            query["session_id"] = session_id
        tasks = list(self.tasks.find(query).sort("created_at", -1))
        for task in tasks:
            task.pop("_id", None)
        return tasks
    
    def get_tasks_by_employee(self, employee_name: str) -> List[Dict[str, Any]]:
        """Get tasks assigned to an employee"""
        tasks = list(self.tasks.find({"assigned_to": employee_name}).sort("created_at", -1))
        for task in tasks:
            task.pop("_id", None)
        return tasks
    
    def update_task_status(self, task_id: str, new_status: str) -> Dict[str, Any]:
        """Update task status"""
        now = datetime.now().isoformat()
        
        update_data = {
            "status": new_status,
            "updated_at": now
        }
        
        # If completing task, set completed_at
        if new_status == "completed":
            update_data["completed_at"] = now
        
        result = self.tasks.update_one(
            {"task_id": task_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            # Get updated task
            task = self.tasks.find_one({"task_id": task_id})
            if task:
                task.pop("_id", None)
                return {
                    "success": True,
                    "message": "Task status updated",
                    "task": task
                }
        
        return {
            "success": False,
            "error": "Task not found"
        }
    
    def get_employee_status(self) -> List[Dict[str, Any]]:
        """Get status summary for all employees"""
        employees = self.get_all_employees()
        status_list = []
        
        for employee in employees:
            employee_name = employee["name"]
            
            # Get tasks by status
            todo_tasks = self.get_tasks_by_employee(employee_name)
            todo_count = len([t for t in todo_tasks if t["status"] == "todo"])
            in_progress_count = len([t for t in todo_tasks if t["status"] == "in_progress"])
            completed_count = len([t for t in todo_tasks if t["status"] == "completed"])
            
            status_list.append({
                "employee_name": employee_name,
                "email": employee.get("email"),
                "todo": todo_count,
                "in_progress": in_progress_count,
                "completed": completed_count,
                "total": len(todo_tasks)
            })
        
        return status_list
    
    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task"""
        result = self.tasks.delete_one({"task_id": task_id})
        
        if result.deleted_count > 0:
            return {
                "success": True,
                "message": "Task deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": "Task not found"
            }
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete session from database"""
        result = self.sessions.delete_one({"session_id": session_id})
        
        if result.deleted_count > 0:
            # Also clear any pending approvals for this session
            self.pending_approvals.delete_many({"session_id": session_id})
            
            return {
                "success": True,
                "message": "Session deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": "Session not found"
            }
    
    # Approval operations
    def add_pending_approval(self, session_id: str, approval_data: Dict[str, Any]) -> None:
        """Add pending approval"""
        now = datetime.now().isoformat()
        
        self.pending_approvals.insert_one({
            "session_id": session_id,
            "approval_data": approval_data,
            "created_at": now
        })
    
    def get_pending_approvals(self, session_id: str) -> List[Dict[str, Any]]:
        """Get pending approvals"""
        approvals = list(self.pending_approvals.find({"session_id": session_id}))
        return [approval["approval_data"] for approval in approvals]
    
    def clear_pending_approvals(self, session_id: str) -> None:
        """Clear pending approvals"""
        self.pending_approvals.delete_many({"session_id": session_id})


# Global database instance
from config import Config
db = Database(Config.MONGODB_URI, Config.MONGODB_DB_NAME)
