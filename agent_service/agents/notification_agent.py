"""
Notification Agent
Sends notifications via Slack and creates Trello cards
"""
from typing import Dict, Any, List
from tools.slack_tools import slack_tools
from tools.trello_tools import trello_tools


class NotificationAgent:
    """
    Notification Agent
    Handles Slack notifications and Trello card creation
    """
    
    def __init__(self):
        self.slack = slack_tools
        self.trello = trello_tools
    
    def create_project_workspace(self, project_name: str, project_description: str) -> Dict[str, Any]:
        """
        Create Slack channel and Trello board for project
        
        Args:
            project_name: Name of the project
            project_description: Project description
        
        Returns:
            Created workspace IDs
        """
        results = {
            "success": True,
            "slack_channel_id": None,
            "trello_board_id": None,
            "errors": []
        }
        
        # Create Slack channel
        channel_name = project_name.lower().replace(" ", "-")
        slack_result = self.slack.create_channel(channel_name, project_description)
        
        if slack_result["success"]:
            results["slack_channel_id"] = slack_result["channel_id"]
        else:
            results["errors"].append(f"Slack: {slack_result['error']}")
        
        # Create Trello board
        trello_result = self.trello.create_board(project_name, project_description)
        
        if trello_result["success"]:
            results["trello_board_id"] = trello_result["board_id"]
        else:
            results["errors"].append(f"Trello: {trello_result['error']}")
        
        if results["errors"]:
            results["success"] = False
        
        return results
    
    def send_approval_request(self, assignment_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send approval request to Slack demo-projects channel
        
        Args:
            assignment_plan: Task allocation plan
        
        Returns:
            Success status
        """
        return self.slack.send_approval_request(assignment_plan)
    
    def execute_assignments(
        self,
        trello_board_id: str,
        assignment_plan: Dict[str, Any],
        employees_data: List[Dict[str, Any]],
        session_id: str = None,
        project_id: str = None
    ) -> Dict[str, Any]:
        """
        Execute approved assignments - create Trello cards, send Slack notifications, and save tasks to database
        
        Args:
            trello_board_id: Trello board ID
            assignment_plan: Approved task allocation plan
            employees_data: List of employee data with emails
            session_id: Session ID for tracking
            project_id: Project ID for tracking
        
        Returns:
            Execution results
        """
        results = {
            "success": True,
            "trello_results": {},
            "slack_results": {},
            "database_results": {},
            "errors": []
        }
        
        assignments = assignment_plan.get("assignments", {})
        
        # Create email lookup
        email_lookup = {emp["name"]: emp["email"] for emp in employees_data}
        
        # Import database
        from database import db
        
        for employee_name, employee_data in assignments.items():
            tasks = employee_data.get("tasks", [])
            employee_email = email_lookup.get(employee_name, "no-email@example.com")
            
            # Save tasks to database
            for task in tasks:
                task_data = {
                    "title": task.get("title", "Untitled Task"),
                    "description": task.get("description", ""),
                    "assigned_to": employee_name,
                    "assigned_to_email": employee_email,
                    "estimated_hours": task.get("estimated_hours", 0),
                    "session_id": session_id,
                    "project_id": project_id
                }
                
                db_result = db.create_task(task_data)
                if not db_result["success"]:
                    results["errors"].append(f"Database for {task.get('title')}: {db_result['error']}")
            
            results["database_results"][employee_name] = {
                "success": True,
                "tasks_created": len(tasks)
            }
            
            # Create Trello cards
            trello_result = self.trello.create_tasks_for_employee(
                board_id=trello_board_id,
                employee_name=employee_name,
                employee_email=employee_email,
                tasks=tasks
            )
            
            results["trello_results"][employee_name] = trello_result
            
            if not trello_result["success"]:
                results["errors"].append(f"Trello for {employee_name}: {trello_result['error']}")
            
            # Send Slack notification to demo-projects channel
            slack_result = self.slack.send_task_assignment(
                employee_name=employee_name,
                employee_email=employee_email,
                tasks=tasks
            )
            
            results["slack_results"][employee_name] = slack_result
            
            if not slack_result["success"]:
                results["errors"].append(f"Slack for {employee_name}: {slack_result['error']}")
        
        if results["errors"]:
            results["success"] = False
        
        return results


# Global instance
notification_agent = NotificationAgent()
