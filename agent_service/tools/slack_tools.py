"""
Slack Integration Tools (MCP-style)
"""
import requests
from typing import Dict, Any
from config import Config


class SlackTools:
    """Slack API integration tools"""
    
    def __init__(self):
        self.token = Config.SLACK_BOT_TOKEN
        self.base_url = "https://slack.com/api"
    
    def create_channel(self, channel_name: str, project_description: str) -> Dict[str, Any]:
        """
        Create a new Slack channel for project
        
        Args:
            channel_name: Name of the channel (lowercase, no spaces)
            project_description: Description of the project
        
        Returns:
            Dict with success status and channel_id
        """
        if not self.token:
            return {
                "success": False,
                "error": "Slack token not configured",
                "channel_id": None
            }
        
        try:
            # Create channel
            response = requests.post(
                f"{self.base_url}/conversations.create",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "name": channel_name,
                    "is_private": False
                }
            )
            
            data = response.json()
            
            if data.get("ok"):
                channel_id = data["channel"]["id"]
                
                # Set channel topic
                requests.post(
                    f"{self.base_url}/conversations.setTopic",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={
                        "channel": channel_id,
                        "topic": project_description
                    }
                )
                
                return {
                    "success": True,
                    "channel_id": channel_id,
                    "channel_name": channel_name
                }
            else:
                return {
                    "success": False,
                    "error": data.get("error", "Unknown error"),
                    "channel_id": None
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "channel_id": None
            }
    
    def send_message(self, channel_id: str, message: str, blocks: list = None) -> Dict[str, Any]:
        """
        Send message to Slack channel
        
        Args:
            channel_id: Slack channel ID
            message: Text message
            blocks: Optional rich message blocks
        
        Returns:
            Dict with success status
        """
        if not self.token:
            return {"success": False, "error": "Slack token not configured"}
        
        try:
            payload = {
                "channel": channel_id,
                "text": message
            }
            
            if blocks:
                payload["blocks"] = blocks
            
            response = requests.post(
                f"{self.base_url}/chat.postMessage",
                headers={"Authorization": f"Bearer {self.token}"},
                json=payload
            )
            
            data = response.json()
            
            return {
                "success": data.get("ok", False),
                "error": data.get("error") if not data.get("ok") else None
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_message_to_channel(self, channel_name: str, message: str, blocks: list = None) -> Dict[str, Any]:
        """
        Send message to Slack channel by name
        
        Args:
            channel_name: Channel name (e.g., "demo-projects")
            message: Text message
            blocks: Optional rich message blocks
        
        Returns:
            Dict with success status
        """
        if not self.token:
            return {"success": False, "error": "Slack token not configured"}
        
        try:
            # Get channel ID by name
            response = requests.get(
                f"{self.base_url}/conversations.list",
                headers={"Authorization": f"Bearer {self.token}"},
                params={"types": "public_channel,private_channel"}
            )
            
            data = response.json()
            channel_id = None
            
            if data.get("ok"):
                for channel in data.get("channels", []):
                    if channel.get("name") == channel_name:
                        channel_id = channel.get("id")
                        break
            
            if not channel_id:
                return {
                    "success": False,
                    "error": f"Channel '{channel_name}' not found"
                }
            
            return self.send_message(channel_id, message, blocks)
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_task_assignment(self, employee_name: str, employee_email: str, tasks: list, channel_name: str = "demo-projects") -> Dict[str, Any]:
        """
        Send task assignment notification to demo-projects channel
        
        Args:
            employee_name: Name of employee
            employee_email: Email of employee
            tasks: List of task dictionaries
            channel_name: Channel name (default: demo-projects)
        
        Returns:
            Dict with success status
        """
        if not self.token:
            return {"success": False, "error": "Slack token not configured"}
        
        try:
            # Get channel ID by name
            response = requests.get(
                f"{self.base_url}/conversations.list",
                headers={"Authorization": f"Bearer {self.token}"},
                params={"types": "public_channel,private_channel"}
            )
            
            data = response.json()
            channel_id = None
            
            if data.get("ok"):
                for channel in data.get("channels", []):
                    if channel.get("name") == channel_name:
                        channel_id = channel.get("id")
                        break
            
            if not channel_id:
                return {
                    "success": False,
                    "error": f"Channel '{channel_name}' not found"
                }
            
            # Format task list
            task_list = "\n".join([
                f"• *{task.get('title', 'Untitled')}* ({task.get('estimated_hours', 0)}h)"
                for task in tasks
            ])
            
            total_hours = sum(task.get('estimated_hours', 0) for task in tasks)
            
            message = f"""📋 *New Task Assignment*

*Assigned to:* {employee_name}
*Email:* {employee_email}
*Total Hours:* {total_hours}h

*Tasks:*
{task_list}

Good luck! 🚀"""
            
            return self.send_message(channel_id, message)
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_approval_request(self, assignment_plan: Dict[str, Any], channel_name: str = "demo-projects") -> Dict[str, Any]:
        """
        Send approval request for task assignments to demo-projects channel
        
        Args:
            assignment_plan: Assignment plan with employee-task mapping
            channel_name: Channel name (default: demo-projects)
        
        Returns:
            Dict with success status
        """
        if not self.token:
            return {"success": False, "error": "Slack token not configured"}
        
        try:
            # Get channel ID by name
            response = requests.get(
                f"{self.base_url}/conversations.list",
                headers={"Authorization": f"Bearer {self.token}"},
                params={"types": "public_channel,private_channel"}
            )
            
            data = response.json()
            channel_id = None
            
            if data.get("ok"):
                for channel in data.get("channels", []):
                    if channel.get("name") == channel_name:
                        channel_id = channel.get("id")
                        break
            
            if not channel_id:
                return {
                    "success": False,
                    "error": f"Channel '{channel_name}' not found"
                }
            
            # Format assignments
            assignments_text = ""
            for employee, data in assignment_plan.get("assignments", {}).items():
                tasks = data.get("tasks", [])
                total_hours = data.get("total_hours", 0)
                task_list = "\n".join([
                    f"  • {task.get('title', 'Untitled')} ({task.get('estimated_hours', 0)}h)"
                    for task in tasks
                ])
                assignments_text += f"\n*{employee}* ({total_hours}h total)\n{task_list}\n"
            
            message = f"""🔔 *Task Assignment Approval Required*
{assignments_text}
Please review and approve in the web interface."""
            
            return self.send_message(channel_id, message)
        
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance
slack_tools = SlackTools()
