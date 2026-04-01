"""
Trello Integration Tools (MCP-style)
"""
import requests
from typing import Dict, Any, List
from config import Config


class TrelloTools:
    """Trello API integration tools"""
    
    def __init__(self):
        self.api_key = Config.TRELLO_API_KEY
        self.token = Config.TRELLO_TOKEN
        self.base_url = "https://api.trello.com/1"
    
    def create_board(self, board_name: str, description: str) -> Dict[str, Any]:
        """
        Create a new Trello board
        
        Args:
            board_name: Name of the board
            description: Board description
        
        Returns:
            Dict with success status and board_id
        """
        if not self.api_key or not self.token:
            return {
                "success": False,
                "error": "Trello credentials not configured",
                "board_id": None
            }
        
        try:
            response = requests.post(
                f"{self.base_url}/boards",
                params={
                    "key": self.api_key,
                    "token": self.token,
                    "name": board_name,
                    "desc": description
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "board_id": data["id"],
                    "board_url": data["url"]
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "board_id": None
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "board_id": None
            }
    
    def create_list(self, board_id: str, list_name: str) -> Dict[str, Any]:
        """
        Create a list on a board
        
        Args:
            board_id: Trello board ID
            list_name: Name of the list
        
        Returns:
            Dict with success status and list_id
        """
        if not self.api_key or not self.token:
            return {"success": False, "error": "Trello credentials not configured"}
        
        try:
            response = requests.post(
                f"{self.base_url}/lists",
                params={
                    "key": self.api_key,
                    "token": self.token,
                    "name": list_name,
                    "idBoard": board_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "list_id": data["id"]
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_card(self, list_id: str, card_name: str, description: str = "", due_date: str = None) -> Dict[str, Any]:
        """
        Create a card in a list
        
        Args:
            list_id: Trello list ID
            card_name: Name of the card
            description: Card description
            due_date: Due date (ISO format)
        
        Returns:
            Dict with success status and card_id
        """
        if not self.api_key or not self.token:
            return {"success": False, "error": "Trello credentials not configured"}
        
        try:
            params = {
                "key": self.api_key,
                "token": self.token,
                "name": card_name,
                "desc": description,
                "idList": list_id
            }
            
            if due_date:
                params["due"] = due_date
            
            response = requests.post(
                f"{self.base_url}/cards",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "card_id": data["id"],
                    "card_url": data["url"]
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def assign_member_to_card(self, card_id: str, member_id: str) -> Dict[str, Any]:
        """
        Assign a member to a card
        
        Args:
            card_id: Trello card ID
            member_id: Trello member ID
        
        Returns:
            Dict with success status
        """
        if not self.api_key or not self.token:
            return {"success": False, "error": "Trello credentials not configured"}
        
        try:
            response = requests.post(
                f"{self.base_url}/cards/{card_id}/idMembers",
                params={
                    "key": self.api_key,
                    "token": self.token,
                    "value": member_id
                }
            )
            
            return {
                "success": response.status_code == 200,
                "error": None if response.status_code == 200 else f"HTTP {response.status_code}"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_tasks_for_employee(self, board_id: str, employee_name: str, employee_email: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a list and cards for an employee's tasks
        
        Args:
            board_id: Trello board ID
            employee_name: Name of employee
            employee_email: Email of employee
            tasks: List of task dictionaries
        
        Returns:
            Dict with success status and created card IDs
        """
        # Create list for employee
        list_name = f"{employee_name} ({employee_email})"
        list_result = self.create_list(board_id, list_name)
        
        if not list_result["success"]:
            return {
                "success": False,
                "error": f"Failed to create list: {list_result['error']}"
            }
        
        list_id = list_result["list_id"]
        created_cards = []
        
        # Create cards for each task
        for task in tasks:
            card_result = self.create_card(
                list_id=list_id,
                card_name=task["title"],
                description=task.get("description", ""),
                due_date=task.get("due_date")
            )
            
            if card_result["success"]:
                created_cards.append({
                    "task_title": task["title"],
                    "card_id": card_result["card_id"],
                    "card_url": card_result["card_url"]
                })
        
        return {
            "success": True,
            "list_id": list_id,
            "created_cards": created_cards
        }


# Global instance
trello_tools = TrelloTools()
