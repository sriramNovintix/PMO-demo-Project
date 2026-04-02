"""
Main Router - Clean architecture with orchestrators
"""
from fastapi import FastAPI


def register_routes(app: FastAPI):
    """
    Register routes to the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.get("/agents")
    def list_agents():
        """List all available orchestrators and agents"""
        return {
            "success": True,
            "architecture": "MCP-Style Clean Architecture",
            "orchestrators": {
                "central": {
                    "name": "Central Orchestrator",
                    "description": "Supervisor that analyzes intent and delegates to sub-orchestrators",
                    "type": "supervisor"
                },
                "project": {
                    "name": "Project Orchestrator",
                    "description": "Handles goals, task generation, skill matching, task allocation",
                    "tools": ["mongodb_tool", "slack_tool"],
                    "sub_agents": ["goal_understanding", "task_generation", "skill_matching", "task_allocation"]
                },
                "recruitment": {
                    "name": "Recruitment Orchestrator",
                    "description": "Handles candidate selection and promotion to employees",
                    "tools": ["mongodb_tool", "slack_tool"],
                    "sub_agents": ["resume_parser", "candidate_selection"]
                },
                "communication": {
                    "name": "Communication Orchestrator",
                    "description": "Handles Slack messages and status updates",
                    "tools": ["mongodb_tool", "slack_tool"],
                    "sub_agents": ["status_agent", "message_formatter"]
                }
            },
            "sub_agents": {
                "goal_understanding": {
                    "name": "Goal Understanding Agent",
                    "description": "Extracts and clarifies project goals",
                    "standalone": True
                },
                "task_generation": {
                    "name": "Task Generation Agent",
                    "description": "Generates tasks from goals",
                    "standalone": True
                },
                "skill_matching": {
                    "name": "Skill Matching Agent",
                    "description": "Matches employee skills to tasks",
                    "standalone": True
                },
                "task_allocation": {
                    "name": "Task Allocation Agent",
                    "description": "Creates optimal allocation plans",
                    "standalone": True
                },
                "status": {
                    "name": "Status Agent",
                    "description": "Provides status updates",
                    "standalone": True
                }
            },
            "tools": {
                "mongodb_tool": {
                    "name": "MongoDB Tool",
                    "description": "Universal database tool for all collections",
                    "operations": ["find", "find_one", "insert", "update", "delete"],
                    "collections": ["employees", "tasks", "candidates", "sessions"]
                },
                "slack_tool": {
                    "name": "Slack Tool",
                    "description": "Universal Slack tool for all operations",
                    "actions": ["send_message", "create_channel", "get_channels"]
                }
            }
        }
    
    @app.get("/")
    def root():
        """Root endpoint with service information"""
        return {
            "status": "online",
            "service": "Task Orchestrator - Agent Service",
            "version": "3.0.0",
            "architecture": "MCP-Style Clean Architecture",
            "description": "Central orchestrator analyzes intent and delegates to specialized sub-orchestrators",
            "features": [
                "MCP-style unified tools (mongodb_tool, slack_tool)",
                "Environment-driven configuration (no hardcoding)",
                "Standalone runnable sub-agents with state management",
                "Sub-orchestrators with specific domains",
                "Central supervisor with intelligent routing",
                "Proper input/output state tracking"
            ],
            "endpoints": {
                "GET /agents": "List all orchestrators and agents",
                "POST /chat": "Main chat endpoint (routes through central orchestrator)",
                "GET /tasks": "Get all tasks",
                "GET /employees": "Get all employees",
                "GET /candidates": "Get all candidates",
                "POST /candidates/upload": "Upload resume",
                "GET /sessions": "Get all sessions",
                "GET /status": "Get employee status",
                "GET /health": "Global health check"
            }
        }
    
    @app.get("/health")
    def health_check():
        """Global health check"""
        return {
            "status": "healthy",
            "service": "Task Orchestrator - Agent Service",
            "version": "3.0.0",
            "architecture": "MCP-Style Clean Architecture",
            "orchestrator": "Central Orchestrator with LangGraph"
        }
