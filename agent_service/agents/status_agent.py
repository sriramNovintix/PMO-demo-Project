"""
Status Agent
Provides status updates for tasks and employees
"""
from typing import Dict, Any
from database import db


class StatusAgent:
    """
    Status Agent - Autonomous
    Retrieves and formats status information
    """
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute status retrieval - autonomous method
        Gets status from database and formats response
        
        Args:
            state: Current state (may contain employee_name for filtering)
        
        Returns:
            Result with status information
        """
        try:
            employee_name = state.get("employee_name")
            
            if employee_name:
                # Get detailed status for specific employee
                result = self.get_detailed_status(employee_name)
            else:
                # Get general status for all employees
                result = self.get_status_update()
            
            if result["success"]:
                return {
                    "success": True,
                    "status_message": result["status_message"],
                    "employee_status": result.get("employee_status", []),
                    "state_updates": {},
                    "message": result["status_message"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error"),
                    "state_updates": {},
                    "message": result["status_message"]
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "state_updates": {},
                "message": f"Error retrieving status: {str(e)}"
            }
    
    def get_status_update(self) -> Dict[str, Any]:
        """
        Get comprehensive status update for all employees and tasks
        
        Returns:
            Status information
        """
        try:
            # Get employee status from database
            employee_status = db.get_employee_status()
            
            # Format status message
            status_message = "📊 **Current Status Update**\n\n"
            
            if not employee_status:
                status_message += "No tasks assigned yet."
                return {
                    "success": True,
                    "status_message": status_message,
                    "employee_status": []
                }
            
            for emp in employee_status:
                status_message += f"**{emp['employee_name']}** ({emp['email']})\n"
                status_message += f"  • To Do: {emp['todo']} tasks\n"
                status_message += f"  • In Progress: {emp['in_progress']} tasks\n"
                status_message += f"  • Completed: {emp['completed']} tasks\n"
                status_message += f"  • Total: {emp['total']} tasks\n\n"
            
            return {
                "success": True,
                "status_message": status_message,
                "employee_status": employee_status
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_message": f"Error retrieving status: {str(e)}"
            }
    
    def get_detailed_status(self, employee_name: str = None) -> Dict[str, Any]:
        """
        Get detailed status with task lists
        
        Args:
            employee_name: Optional employee name to filter
        
        Returns:
            Detailed status information
        """
        try:
            if employee_name:
                # Get tasks for specific employee
                tasks = db.get_tasks_by_employee(employee_name)
            else:
                # Get all tasks
                tasks = db.get_all_tasks()
            
            # Group by status
            todo_tasks = [t for t in tasks if t["status"] == "todo"]
            in_progress_tasks = [t for t in tasks if t["status"] == "in_progress"]
            completed_tasks = [t for t in tasks if t["status"] == "completed"]
            
            status_message = f"📋 **Detailed Status**"
            if employee_name:
                status_message += f" for {employee_name}"
            status_message += "\n\n"
            
            # To Do
            status_message += f"**📝 To Do ({len(todo_tasks)})**\n"
            for task in todo_tasks[:5]:  # Limit to 5
                status_message += f"  • {task['title']} ({task['estimated_hours']}h)\n"
            if len(todo_tasks) > 5:
                status_message += f"  ... and {len(todo_tasks) - 5} more\n"
            status_message += "\n"
            
            # In Progress
            status_message += f"**🔄 In Progress ({len(in_progress_tasks)})**\n"
            for task in in_progress_tasks[:5]:
                status_message += f"  • {task['title']} ({task['estimated_hours']}h)\n"
            if len(in_progress_tasks) > 5:
                status_message += f"  ... and {len(in_progress_tasks) - 5} more\n"
            status_message += "\n"
            
            # Completed
            status_message += f"**✅ Completed ({len(completed_tasks)})**\n"
            for task in completed_tasks[:5]:
                status_message += f"  • {task['title']} ({task['estimated_hours']}h)\n"
            if len(completed_tasks) > 5:
                status_message += f"  ... and {len(completed_tasks) - 5} more\n"
            
            return {
                "success": True,
                "status_message": status_message,
                "todo": len(todo_tasks),
                "in_progress": len(in_progress_tasks),
                "completed": len(completed_tasks)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_message": f"Error retrieving detailed status: {str(e)}"
            }


# Global instance
status_agent = StatusAgent()
