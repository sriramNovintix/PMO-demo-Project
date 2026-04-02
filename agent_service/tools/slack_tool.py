"""
Slack Tool (MCP-style)
Single unified tool for all Slack operations
"""
from langchain_core.tools import tool
import requests
from config import Config
import json


@tool
def slack_tool(action: str, channel: str = "demo-projects", message: str = None, **kwargs) -> str:
    """
    Universal Slack tool for all Slack operations.
    
    Args:
        action: Action type - "send_message", "create_channel", "get_channels"
        channel: Channel name (default: "demo-projects")
        message: Message text for send_message action
        **kwargs: Additional parameters (e.g., blocks, topic, is_private)
    
    Returns:
        JSON string with operation result
    
    Examples:
        - Send message: slack_tool("send_message", "demo-projects", "Hello team!")
        - Create channel: slack_tool("create_channel", "new-project", topic="Project discussion")
        - Get channels: slack_tool("get_channels")
    """
    try:
        token = Config.SLACK_BOT_TOKEN
        if not token:
            return json.dumps({"success": False, "error": "Slack token not configured"})
        
        base_url = "https://slack.com/api"
        
        if action == "send_message":
            if not message:
                return json.dumps({"success": False, "error": "Message required for send_message"})
            
            # Get channel ID by name
            response = requests.get(
                f"{base_url}/conversations.list",
                headers={"Authorization": f"Bearer {token}"},
                params={"types": "public_channel,private_channel"}
            )
            
            data = response.json()
            channel_id = None
            
            if data.get("ok"):
                for ch in data.get("channels", []):
                    if ch.get("name") == channel:
                        channel_id = ch.get("id")
                        break
            
            if not channel_id:
                return json.dumps({"success": False, "error": f"Channel '{channel}' not found"})
            
            # Send message
            payload = {
                "channel": channel_id,
                "text": message
            }
            
            if kwargs.get("blocks"):
                payload["blocks"] = kwargs["blocks"]
            
            response = requests.post(
                f"{base_url}/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                json=payload
            )
            
            result = response.json()
            return json.dumps({
                "success": result.get("ok", False),
                "error": result.get("error") if not result.get("ok") else None,
                "channel": channel,
                "message_sent": message[:50] + "..." if len(message) > 50 else message
            }, indent=2)
        
        elif action == "create_channel":
            # Create channel
            response = requests.post(
                f"{base_url}/conversations.create",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": channel,
                    "is_private": kwargs.get("is_private", False)
                }
            )
            
            result = response.json()
            
            if result.get("ok"):
                channel_id = result["channel"]["id"]
                
                # Set topic if provided
                if kwargs.get("topic"):
                    requests.post(
                        f"{base_url}/conversations.setTopic",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "channel": channel_id,
                            "topic": kwargs["topic"]
                        }
                    )
                
                return json.dumps({
                    "success": True,
                    "channel_id": channel_id,
                    "channel_name": channel
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }, indent=2)
        
        elif action == "get_channels":
            response = requests.get(
                f"{base_url}/conversations.list",
                headers={"Authorization": f"Bearer {token}"},
                params={"types": "public_channel,private_channel"}
            )
            
            result = response.json()
            
            if result.get("ok"):
                channels = [
                    {"id": ch["id"], "name": ch["name"]}
                    for ch in result.get("channels", [])
                ]
                return json.dumps({
                    "success": True,
                    "channels": channels,
                    "count": len(channels)
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }, indent=2)
        
        else:
            return json.dumps({"success": False, "error": f"Unknown action: {action}"})
    
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
