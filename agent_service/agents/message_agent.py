"""
Message Agent
Handles Slack messaging with context-aware message generation
"""
from typing import Dict, Any
from tools.slack_tools import slack_tools
from database import db
from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, invoke_with_prompt


class MessageAgent:
    """
    Message Agent - Autonomous
    Generates and sends contextual messages to Slack based on manager intent
    """
    
    def __init__(self):
        self.slack = slack_tools
        self.llm = get_llm()
        self.message_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Message Generation Agent.
Generate professional Slack messages based on the manager's intent and context.

Guidelines:
- Be clear and concise
- Include relevant details (employee names, task titles, status)
- Use appropriate emojis for readability
- Format for Slack (use *bold*, _italic_, bullet points)
- Keep tone professional but friendly

Respond with ONLY the message text, no JSON or extra formatting."""),
            ("human", """Manager Intent: {intent}

Context:
{context}

Generate an appropriate Slack message.""")
        ])
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute message sending - autonomous method
        Determines intent, generates message, and sends to Slack
        
        Args:
            state: Current state with user_message and workflow_type
        
        Returns:
            Result with success status and message
        """
        try:
            workflow_type = state.get("workflow_type")
            user_message = state.get("user_message", "").lower()
            
            if workflow_type == "SEND_STATUS":
                # Send status report
                result = self.send_status_report()
                
                return {
                    "success": result["success"],
                    "state_updates": {},
                    "message": result["message"],
                    "channel": result.get("channel"),
                    "report": result.get("report")
                }
            
            elif workflow_type == "SEND_MESSAGE":
                # Extract employee name from message
                employee_name = None
                if "sriram" in user_message:
                    employee_name = "sriram"
                # Add more employee name detection as needed
                
                # Determine intent
                intent = user_message
                if "update" in user_message:
                    intent = f"Send task update for {employee_name}" if employee_name else "Send general update"
                elif "status" in user_message:
                    intent = f"Send status for {employee_name}" if employee_name else "Send status report"
                elif "task" in user_message and "list" in user_message:
                    intent = "Send complete task list to team"
                
                # Generate and send message
                result = self.generate_and_send_message(
                    intent=intent,
                    employee_name=employee_name
                )
                
                return {
                    "success": result["success"],
                    "state_updates": {},
                    "message": result["message"],
                    "channel": result.get("channel"),
                    "generated_message": result.get("generated_message")
                }
            
            else:
                return {
                    "success": False,
                    "error": "Unknown workflow type",
                    "state_updates": {},
                    "message": "Unable to determine message intent"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "state_updates": {},
                "message": f"Error: {str(e)}"
            }
    
    def generate_and_send_message(self, intent: str, employee_name: str = None, channel_name: str = "demo-projects") -> Dict[str, Any]:
        """
        Generate contextual message and send to Slack
        
        Args:
            intent: Manager's intent (e.g., "send update", "send status")
            employee_name: Optional employee name to filter tasks
            channel_name: Slack channel name
        
        Returns:
            Success status and generated message
        """
        try:
            # Build context based on intent
            context = self._build_context(intent, employee_name)
            
            # Generate message using LLM
            response = invoke_with_prompt(
                self.message_prompt,
                self.llm,
                intent=intent,
                context=context
            )
            
            message = response.content.strip()
            
            # Send to Slack
            result = self.slack.send_message_to_channel(
                channel_name=channel_name,
                message=message
            )
            
            return {
                "success": result["success"],
                "message": "Message sent to Slack" if result["success"] else result["error"],
                "channel": channel_name,
                "generated_message": message
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate/send message: {str(e)}"
            }
    
    def _build_context(self, intent: str, employee_name: str = None) -> str:
        """Build context for message generation - fetches from MongoDB"""
        context_parts = []
        
        # Get tasks from database (ALL tasks, not session-specific)
        if employee_name:
            tasks = db.get_tasks_by_employee(employee_name)
            if not tasks:
                context_parts.append(f"Employee: {employee_name}")
                context_parts.append("No tasks found for this employee")
                return "\n".join(context_parts)
            
            context_parts.append(f"Employee: {employee_name}")
            context_parts.append(f"Total Tasks: {len(tasks)}")
            
            # Group by status
            todo = [t for t in tasks if t['status'] == 'todo']
            in_progress = [t for t in tasks if t['status'] == 'in_progress']
            completed = [t for t in tasks if t['status'] == 'completed']
            
            if todo:
                context_parts.append(f"\nTo Do ({len(todo)}):")
                for t in todo[:5]:
                    context_parts.append(f"  - {t['title']} ({t['estimated_hours']}h)")
            
            if in_progress:
                context_parts.append(f"\nIn Progress ({len(in_progress)}):")
                for t in in_progress[:5]:
                    context_parts.append(f"  - {t['title']} ({t['estimated_hours']}h)")
            
            if completed:
                context_parts.append(f"\nCompleted ({len(completed)}):")
                for t in completed[:5]:
                    context_parts.append(f"  - {t['title']} ({t['estimated_hours']}h)")
        else:
            # Get ALL tasks from MongoDB (not session-specific)
            all_tasks = db.get_all_tasks()
            
            if not all_tasks:
                context_parts.append("No tasks found in the system")
                return "\n".join(context_parts)
            
            context_parts.append(f"Total Tasks in System: {len(all_tasks)}")
            
            # Group by status
            todo = [t for t in all_tasks if t['status'] == 'todo']
            in_progress = [t for t in all_tasks if t['status'] == 'in_progress']
            completed = [t for t in all_tasks if t['status'] == 'completed']
            
            context_parts.append(f"\nTo Do: {len(todo)} tasks")
            context_parts.append(f"In Progress: {len(in_progress)} tasks")
            context_parts.append(f"Completed: {len(completed)} tasks")
            
            # Show sample tasks
            context_parts.append("\nSample Tasks:")
            for t in all_tasks[:10]:
                assigned = t.get('assigned_to', 'Unassigned')
                context_parts.append(f"  - {t['title']} ({t['estimated_hours']}h) - {assigned} [{t['status']}]")
            
            # Get employee status
            employee_status = db.get_employee_status()
            if employee_status:
                context_parts.append(f"\nEmployees: {len(employee_status)}")
                for emp in employee_status:
                    context_parts.append(f"  - {emp['employee_name']}: {emp['total']} tasks ({emp['completed']} completed)")
        
        return "\n".join(context_parts)
    
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
