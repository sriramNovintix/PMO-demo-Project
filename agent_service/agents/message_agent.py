"""
Message Agent
Handles Slack messaging
"""
from typing import Dict, Any
from tools.slack_tools import slack_tools
from database import db


class MessageAgent:
    """
    Message Agent
    Sends messages and status reports to Slack
    """
    
    def __init__(self):
        self.slack = slack_tools
    
    def send_custom_message(self, message: str, channel_name: str = "demo-projects") -> Dict[str, Any]:
        """
        Send custom message to Slack
        
        Args:
            message: Message to send
            channel_name: Slack channel name
        
        Returns:
            Success status
        """
        try:
            result = self.slack.send_message_to_channel(
                channel_name=channel_name,
                message=message
            )
            
            return {
                "success": result["success"],
                "message": "Message sent to Slack" if result["success"] else result["error"],
                "channel": channel_name
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to send message: {str(e)}"
            }
    
    def send_status_report(self, channel_name: str = "demo-projects") -> Dict[str, Any]:
        """
        Send comprehensive status report to Slack
        
        Args:
            channel_name: Slack channel name
        
        Returns:
            Success status
        """
        try:
            # Get employee status
            employee_status = db.get_employee_status()
            
            if not employee_status:
                message = "📊 **Status Report**\n\nNo tasks assigned yet."
            else:
                message = "📊 **Status Report**\n\n"
                
                for emp in employee_status:
                    # Get detailed tasks
                    tasks = db.get_tasks_by_employee(emp['employee_name'])
                    
                    pending_tasks = [t for t in tasks if t['status'] in ['todo', 'in_progress']]
                    completed_tasks = [t for t in tasks if t['status'] == 'completed']
                    
                    message += f"*{emp['employee_name']}* ({emp['email']})\n"
                    
                    # Pending tasks
                    if pending_tasks:
                        message += f"  📋 *Pending Tasks ({len(pending_tasks)}):*\n"
                        for task in pending_tasks[:3]:  # Limit to 3
                            status_emoji = "📝" if task['status'] == 'todo' else "🔄"
                            message += f"    {status_emoji} {task['title']} ({task['estimated_hours']}h)\n"
                        if len(pending_tasks) > 3:
                            message += f"    ... and {len(pending_tasks) - 3} more\n"
                    
                    # Completed tasks
                    if completed_tasks:
                        message += f"  ✅ *Completed Tasks ({len(completed_tasks)}):*\n"
                        for task in completed_tasks[:3]:
                            message += f"    • {task['title']} ({task['estimated_hours']}h)\n"
                        if len(completed_tasks) > 3:
                            message += f"    ... and {len(completed_tasks) - 3} more\n"
                    
                    message += "\n"
            
            # Send to Slack
            result = self.slack.send_message_to_channel(
                channel_name=channel_name,
                message=message
            )
            
            return {
                "success": result["success"],
                "message": "Status report sent to Slack" if result["success"] else result["error"],
                "channel": channel_name,
                "report": message
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to send status report: {str(e)}"
            }


# Global instance
message_agent = MessageAgent()
