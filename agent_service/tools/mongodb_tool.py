"""
MongoDB Tool (MCP-style)
Single unified tool for all database operations
"""
from langchain_core.tools import tool
from database import db
import json
from typing import Optional
from agentops.sdk.decorators import tool as agentops_tool


@tool
@agentops_tool(name="mongodb_tool", cost=0.0)
def mongodb_tool(operation: str, collection: str, data: dict = None, query: dict = None) -> str:
    """
    Universal MongoDB tool for all database operations.
    
    Args:
        operation: Operation type - "find", "find_one", "insert", "update", "delete", "count"
        collection: Collection name - "employees", "tasks", "candidates", "sessions"
        data: Data for insert/update operations
        query: Query filter for find/update/delete operations
    
    Returns:
        JSON string with operation result
    
    Examples:
        - Get all employees: mongodb_tool("find", "employees")
        - Get specific employee: mongodb_tool("find_one", "employees", query={"name": "John"})
        - Get unassigned tasks: mongodb_tool("find", "tasks", query={"assigned_to": None})
        - Insert employee: mongodb_tool("insert", "employees", data={"name": "John", "skills": ["Python"]})
        - Update task: mongodb_tool("update", "tasks", query={"task_id": "123"}, data={"status": "completed"})
    """
    try:
        if collection == "employees":
            if operation == "find":
                employees = db.get_all_employees()
                if query:
                    # Filter employees based on query
                    filtered = []
                    for emp in employees:
                        match = all(emp.get(k) == v for k, v in query.items())
                        if match:
                            filtered.append(emp)
                    employees = filtered
                return json.dumps({"success": True, "data": employees, "count": len(employees)}, indent=2)
            
            elif operation == "find_one":
                employees = db.get_all_employees()
                if query:
                    for emp in employees:
                        match = all(emp.get(k) == v for k, v in query.items())
                        if match:
                            return json.dumps({"success": True, "data": emp}, indent=2)
                return json.dumps({"success": False, "error": "Employee not found"})
            
            elif operation == "insert":
                if not data:
                    return json.dumps({"success": False, "error": "Data required for insert"})
                result = db.add_employee(data)
                return json.dumps(result, indent=2)
            
            elif operation == "delete":
                if not query or "employee_id" not in query:
                    return json.dumps({"success": False, "error": "employee_id required for delete"})
                result = db.delete_employee(query["employee_id"])
                return json.dumps(result, indent=2)
        
        elif collection == "tasks":
            if operation == "find":
                session_id = query.get("session_id") if query else None
                tasks = db.get_all_tasks(session_id)
                
                if query:
                    # Filter tasks based on query
                    filtered = []
                    for task in tasks:
                        match = all(
                            task.get(k) == v if v is not None else task.get(k) is None
                            for k, v in query.items()
                        )
                        if match:
                            filtered.append(task)
                    tasks = filtered
                
                return json.dumps({"success": True, "data": tasks, "count": len(tasks)}, indent=2)
            
            elif operation == "find_one":
                tasks = db.get_all_tasks()
                if query:
                    for task in tasks:
                        match = all(task.get(k) == v for k, v in query.items())
                        if match:
                            return json.dumps({"success": True, "data": task}, indent=2)
                return json.dumps({"success": False, "error": "Task not found"})
            
            elif operation == "insert":
                if not data:
                    return json.dumps({"success": False, "error": "Data required for insert"})
                
                # Ensure assigned_to is employee NAME, not email
                if "assigned_to" in data and "@" in str(data.get("assigned_to", "")):
                    # If email provided, find employee name
                    employees = db.get_all_employees()
                    for emp in employees:
                        if emp.get("email") == data["assigned_to"]:
                            data["assigned_to"] = emp["name"]
                            data["assigned_to_email"] = emp.get("email")
                            break
                
                result = db.create_task(data)
                return json.dumps(result, indent=2)
            
            elif operation == "update":
                if not query or "task_id" not in query:
                    return json.dumps({"success": False, "error": "task_id required for update"})
                if not data:
                    return json.dumps({"success": False, "error": "Data required for update"})
                
                # Ensure assigned_to is employee NAME, not email
                if "assigned_to" in data:
                    assigned_value = data["assigned_to"]
                    if "@" in str(assigned_value):
                        # If email provided, find employee name
                        employees = db.get_all_employees()
                        for emp in employees:
                            if emp.get("email") == assigned_value:
                                data["assigned_to"] = emp["name"]
                                data["assigned_to_email"] = emp.get("email")
                                break
                    else:
                        # If name provided, find email
                        employees = db.get_all_employees()
                        for emp in employees:
                            if emp["name"].lower().strip() == str(assigned_value).lower().strip():
                                data["assigned_to"] = emp["name"]
                                data["assigned_to_email"] = emp.get("email")
                                break
                
                # Update task status if provided
                if "status" in data:
                    result = db.update_task_status(query["task_id"], data["status"])
                    return json.dumps(result, indent=2)
                
                # General update
                from datetime import datetime
                db.tasks.update_one(
                    {"task_id": query["task_id"]},
                    {"$set": {**data, "updated_at": datetime.now().isoformat()}}
                )
                return json.dumps({"success": True, "message": "Task updated"}, indent=2)
            
            elif operation == "delete":
                if not query or "task_id" not in query:
                    return json.dumps({"success": False, "error": "task_id required for delete"})
                result = db.delete_task(query["task_id"])
                return json.dumps(result, indent=2)
        
        elif collection == "candidates":
            if operation == "find":
                candidates = db.get_all_candidates()
                if query:
                    filtered = []
                    for cand in candidates:
                        match = all(cand.get(k) == v for k, v in query.items())
                        if match:
                            filtered.append(cand)
                    candidates = filtered
                return json.dumps({"success": True, "data": candidates, "count": len(candidates)}, indent=2)
            
            elif operation == "insert":
                if not data:
                    return json.dumps({"success": False, "error": "Data required for insert"})
                result = db.add_candidate(data)
                return json.dumps(result, indent=2)
            
            elif operation == "delete":
                if not query or "candidate_id" not in query:
                    return json.dumps({"success": False, "error": "candidate_id required for delete"})
                result = db.reject_candidate(query["candidate_id"])
                return json.dumps(result, indent=2)
        
        elif collection == "sessions":
            if operation == "find":
                sessions = db.get_all_sessions()
                return json.dumps({"success": True, "data": sessions, "count": len(sessions)}, indent=2)
            
            elif operation == "find_one":
                if not query or "session_id" not in query:
                    return json.dumps({"success": False, "error": "session_id required"})
                state = db.get_session_state(query["session_id"])
                if state:
                    return json.dumps({"success": True, "data": state}, indent=2)
                return json.dumps({"success": False, "error": "Session not found"})
        
        else:
            return json.dumps({"success": False, "error": f"Unknown collection: {collection}"})
    
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
