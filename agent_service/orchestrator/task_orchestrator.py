"""
Non-Deterministic Task Orchestrator
Uses LangGraph for dynamic agent coordination

ARCHITECTURE:
- All agents are autonomous and self-contained
- Each agent has an execute(state) method that:
  * Fetches its own data from DB/tools when needed
  * Manages its own state
  * Returns results with state_updates
  * Can be tested independently
- Orchestrator nodes simply call agent.execute(state) and merge state_updates
- Tools are used internally by agents, not exposed in orchestrator
- Controller agent routes to appropriate agents based on user intent
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from state import (
    AgentState, 
    create_initial_state, 
    add_agent_message, 
    mark_agent_completed,
    add_to_conversation_history,
    get_conversation_context
)
from memory.session_memory import memory

# Import agents
from agents.controller_agent import controller_agent
from agents.goal_understanding_agent import goal_understanding_agent
from agents.task_generation_agent import task_generation_agent
from agents.skill_matching_agent import skill_matching_agent
from agents.task_allocation_agent import task_allocation_agent
from agents.status_agent import status_agent
from agents.message_agent import message_agent


class TaskOrchestrator:
    """
    Non-deterministic orchestrator with autonomous agents
    
    Controller agent decides next steps dynamically.
    All agents are self-contained and testable independently.
    Orchestrator nodes use generic pattern: agent.execute(state) → merge state_updates
    """
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the orchestration graph"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("controller", self._controller_node)
        workflow.add_node("goal_understanding", self._goal_understanding_node)
        workflow.add_node("task_generation", self._task_generation_node)
        workflow.add_node("skill_matching", self._skill_matching_node)
        workflow.add_node("task_allocation", self._task_allocation_node)
        workflow.add_node("status", self._status_node)
        workflow.add_node("message", self._message_node)
        workflow.add_node("human_approval", self._human_approval_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Set entry point
        workflow.set_entry_point("controller")
        
        # Controller decides next agent dynamically
        workflow.add_conditional_edges(
            "controller",
            self._route_next,
            {
                "goal_understanding": "goal_understanding",
                "task_generation": "task_generation",
                "skill_matching": "skill_matching",
                "task_allocation": "task_allocation",
                "status": "status",
                "message": "message",
                "human_approval": "human_approval",
                "finalize": "finalize",
                "end": END
            }
        )
        
        # All agents return to controller
        workflow.add_edge("goal_understanding", "controller")
        workflow.add_edge("task_generation", "controller")
        workflow.add_edge("skill_matching", "controller")
        workflow.add_edge("task_allocation", "controller")
        workflow.add_edge("status", "controller")
        workflow.add_edge("message", "controller")
        workflow.add_edge("human_approval", "controller")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _controller_node(self, state: AgentState) -> AgentState:
        """Controller agent - decides next action"""
        print(f"\n🎯 CONTROLLER AGENT")
        print(f"   Session: {state['session_id']}")
        print(f"   User Message: {state.get('user_message', '')[:100]}")
        print(f"   Project: {state.get('project_name')}")
        print(f"   Goal: {state.get('weekly_goal')}")
        print(f"   Tasks: {len(state.get('generated_tasks', []))}")
        print(f"   Completed: {state['completed_agents']}")
        
        # Check for infinite loops
        agent_messages = state.get("agent_messages", [])
        if len(agent_messages) > 20:
            print(f"   ⚠️ WARNING: Too many agent messages ({len(agent_messages)}), stopping")
            state["next_agent"] = "finalize"
            state["response_to_user"] = "I apologize, but I'm having trouble processing your request. Let me summarize what we have so far."
            return state
        
        # Check if controller has been called too many times in a row
        recent_controllers = [msg for msg in agent_messages[-10:] if msg.get("from") == "controller"]
        if len(recent_controllers) > 5:
            print(f"   ⚠️ WARNING: Controller called {len(recent_controllers)} times recently, forcing finalize")
            state["next_agent"] = "finalize"
            
            # Build summary response
            summary = "Here's what we have:\n"
            if state.get("project_name"):
                summary += f"• Project: {state['project_name']}\n"
            if state.get("weekly_goal"):
                summary += f"• Goal: {state['weekly_goal']}\n"
            if state.get("generated_tasks"):
                summary += f"• Tasks: {len(state['generated_tasks'])} generated\n"
            
            state["response_to_user"] = summary
            return state
        
        # Controller makes decision
        decision = controller_agent.decide_next_action(state)
        
        if decision["success"]:
            state["next_agent"] = decision["next_agent"]
            state["workflow_type"] = decision.get("workflow_type")
            state["response_to_user"] = decision.get("response_to_user", "")
            
            add_agent_message(
                state,
                "controller",
                decision["next_agent"],
                decision["reasoning"],
                {"workflow": decision.get("workflow_type")}
            )
            
            print(f"   ✅ Decision: {decision['next_agent']}")
            print(f"   Workflow: {decision.get('workflow_type')}")
            print(f"   Reasoning: {decision['reasoning']}")
        else:
            state["next_agent"] = "end"
            state["response_to_user"] = decision.get("response_to_user", "Error occurred")
            print(f"   ❌ Error: {decision.get('error')}")
        
        return state
    
    def _goal_understanding_node(self, state: AgentState) -> AgentState:
        """Goal understanding agent - simplified"""
        print(f"\n📋 GOAL UNDERSTANDING AGENT")
        
        # Call agent's execute method
        result = goal_understanding_agent.execute(state)
        
        if result["success"]:
            # Update state with agent's state_updates
            state.update(result.get("state_updates", {}))
            state["response_to_user"] = result.get("message", "")
            
            # Store in memory immediately
            memory.store_state(state["session_id"], state)
            print(f"   💾 State saved to memory")
            
            add_agent_message(
                state,
                "goal_understanding",
                "controller",
                result.get("message", "Goal extracted"),
                result.get("extracted_data", {})
            )
            
            print(f"   ✅ {result.get('message')}")
            print(f"   Final state - Project: {state.get('project_name')}, Goal: {state.get('weekly_goal')}")
        else:
            add_agent_message(
                state,
                "goal_understanding",
                "controller",
                f"Error: {result.get('error')}"
            )
            print(f"   ❌ Error: {result.get('error')}")
        
        mark_agent_completed(state, "goal_understanding")
        return state
    
    def _task_generation_node(self, state: AgentState) -> AgentState:
        """Task generation agent - simplified"""
        print(f"\n📝 TASK GENERATION AGENT")
        
        # Call agent's execute method
        result = task_generation_agent.execute(state)
        
        if result["success"]:
            # Update state with agent's state_updates
            state.update(result.get("state_updates", {}))
            state["response_to_user"] = result.get("message", "")
            
            add_agent_message(
                state,
                "task_generation",
                "controller",
                result.get("message", "Tasks generated"),
                {
                    "tasks": result.get("tasks", []),
                    "total_hours": result.get("total_estimated_hours", 0)
                }
            )
            
            print(f"   ✅ {result.get('message')}")
        else:
            add_agent_message(
                state,
                "task_generation",
                "controller",
                f"Error: {result.get('error')}"
            )
            print(f"   ❌ Error: {result.get('error')}")
        
        mark_agent_completed(state, "task_generation")
        return state
    
    def _skill_matching_node(self, state: AgentState) -> AgentState:
        """Skill matching agent - simplified"""
        print(f"\n🎯 SKILL MATCHING AGENT")
        
        # Call agent's execute method
        result = skill_matching_agent.execute(state)
        
        if result["success"]:
            # Update state with agent's state_updates
            state.update(result.get("state_updates", {}))
            state["response_to_user"] = result.get("message", "")
            
            add_agent_message(
                state,
                "skill_matching",
                "controller",
                result.get("message", "Skill matching completed"),
                {"task_matches": result.get("task_matches", [])}
            )
            
            print(f"   ✅ {result.get('message')}")
        else:
            add_agent_message(
                state,
                "skill_matching",
                "controller",
                f"Error: {result.get('error')}"
            )
            state["response_to_user"] = result.get("message", "Skill matching failed")
            print(f"   ❌ Error: {result.get('error')}")
        
        mark_agent_completed(state, "skill_matching")
        return state
    
    def _task_allocation_node(self, state: AgentState) -> AgentState:
        """Task allocation agent - simplified"""
        print(f"\n📊 TASK ALLOCATION AGENT")
        
        # Call agent's execute method
        result = task_allocation_agent.execute(state)
        
        if result["success"]:
            # Update state with agent's state_updates
            state.update(result.get("state_updates", {}))
            state["response_to_user"] = result.get("message", "")
            
            add_agent_message(
                state,
                "task_allocation",
                "controller",
                result.get("message", "Tasks allocated"),
                result.get("assignment_plan", {})
            )
            
            print(f"   ✅ {result.get('message')}")
        else:
            add_agent_message(
                state,
                "task_allocation",
                "controller",
                f"Error: {result.get('error')}"
            )
            print(f"   ❌ Error: {result.get('error')}")
        
        mark_agent_completed(state, "task_allocation")
        return state
    
    def _status_node(self, state: AgentState) -> AgentState:
        """Status agent - simplified"""
        print(f"\n📊 STATUS AGENT")
        
        # Call agent's execute method
        result = status_agent.execute(state)
        
        if result["success"]:
            state["response_to_user"] = result.get("message", "")
            
            add_agent_message(
                state,
                "status",
                "controller",
                "Status retrieved",
                {
                    "employee_status": result.get("employee_status", [])
                }
            )
            
            print(f"   ✅ Status retrieved")
        else:
            state["response_to_user"] = result.get("message", "")
            add_agent_message(
                state,
                "status",
                "controller",
                f"Error: {result.get('error')}"
            )
            print(f"   ❌ Error: {result.get('error')}")
        
        mark_agent_completed(state, "status")
        return state
    
    def _message_node(self, state: AgentState) -> AgentState:
        """Message agent - simplified"""
        print(f"\n💬 MESSAGE AGENT")
        
        # Call agent's execute method
        result = message_agent.execute(state)
        
        if result["success"]:
            state["response_to_user"] = result.get("message", "")
            
            add_agent_message(
                state,
                "message",
                "controller",
                result.get("message", "Message sent"),
                {
                    "channel": result.get("channel"),
                    "generated_message": result.get("generated_message")
                }
            )
            
            print(f"   ✅ {result.get('message')}")
        else:
            state["response_to_user"] = result.get("message", "")
            add_agent_message(
                state,
                "message",
                "controller",
                f"Error: {result.get('error')}"
            )
            print(f"   ❌ Error: {result.get('error')}")
        
        mark_agent_completed(state, "message")
        return state
    
    def _human_approval_node(self, state: AgentState) -> AgentState:
        """Human approval checkpoint"""
        print(f"\n👤 HUMAN APPROVAL REQUIRED")
        
        if state.get("pending_approval") and state.get("assignment_plan"):
            # Send approval request to Slack (no channel_id needed - uses default channel)
            notification_agent.send_approval_request(
                state["assignment_plan"]
            )
            
            # Store pending approval in memory
            memory.add_pending_approval(state["session_id"], {
                "assignment_plan": state["assignment_plan"],
                "timestamp": state["last_updated"]
            })
            
            state["response_to_user"] = "Task allocation plan created. Please review and approve."
            
            add_agent_message(
                state,
                "human_approval",
                "controller",
                "Waiting for human approval"
            )
            
            print(f"   Approval request sent")
        
        mark_agent_completed(state, "human_approval")
        return state
    
    def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalize and prepare response"""
        print(f"\n✅ FINALIZING")
        print(f"   Project: {state.get('project_name')}")
        print(f"   Goal: {state.get('weekly_goal')}")
        print(f"   Tasks: {len(state.get('generated_tasks', []))}")
        
        # Store final state in memory
        memory.store_state(state["session_id"], state)
        
        # Build response if not already set
        if not state.get("response_to_user"):
            response = ""
            
            # Add project and goal info
            if state.get("project_name"):
                response += f"📋 Project: {state['project_name']}\n"
            if state.get("weekly_goal"):
                response += f"🎯 Goal: {state['weekly_goal']}\n"
            
            # Get tasks from database (more reliable than state)
            from database import db
            session_id = state.get("session_id")
            db_tasks = db.get_all_tasks(session_id) if session_id else []
            
            # Use database tasks if available, otherwise use state tasks
            tasks = db_tasks if db_tasks else state.get("generated_tasks", [])
            
            # Add task information if tasks exist
            if tasks:
                response += f"\n✅ Generated {len(tasks)} tasks:\n\n"
                for i, task in enumerate(tasks, 1):  # Show all tasks
                    title = task.get('title', 'Untitled')
                    hours = task.get('estimated_hours', 0)
                    priority = task.get('priority', 'medium')
                    assigned_to = task.get('assigned_to', 'Unassigned')
                    status = task.get('status', 'todo')
                    
                    response += f"{i}. {title}\n"
                    response += f"   • Duration: {hours}h | Priority: {priority}\n"
                    response += f"   • Assigned: {assigned_to} | Status: {status}\n"
                    
                    # Show skills if available
                    skills = task.get('required_skills', [])
                    if skills:
                        skills_str = ', '.join(skills[:3])
                        response += f"   • Skills: {skills_str}\n"
                    response += "\n"
            else:
                response += "\n✅ Request processed successfully."
            
            state["response_to_user"] = response
        
        print(f"   Response: {state['response_to_user'][:100]}")
        
        return state
    
    def _route_next(self, state: AgentState) -> str:
        """Route to next agent based on controller decision"""
        next_agent = state.get("next_agent", "end")
        
        # Map agent names to node names
        agent_map = {
            "goal_understanding": "goal_understanding",
            "task_generation": "task_generation",
            "skill_matching": "skill_matching",
            "task_allocation": "task_allocation",
            "notification": "notification",
            "status": "status",
            "message": "message",
            "human_approval": "human_approval",
            "none": "finalize",
            "end": "end"
        }
        
        return agent_map.get(next_agent, "end")
    
    def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process user message through orchestrator
        
        Args:
            session_id: Session identifier
            user_message: User's message
        
        Returns:
            Response with agent decisions and results
        """
        print(f"\n{'='*60}")
        print(f"🚀 PROCESSING MESSAGE")
        print(f"   Session: {session_id}")
        print(f"   Message: {user_message[:100]}")
        print(f"{'='*60}")
        
        # Create or retrieve session
        memory.create_session(session_id)
        
        # Get previous state if exists
        previous_state = memory.get_latest_state(session_id)
        
        # Create initial state
        if previous_state:
            # Continue from previous state
            print(f"📦 Loading previous state:")
            print(f"   Project: {previous_state.get('project_name')}")
            print(f"   Goal: {previous_state.get('weekly_goal')}")
            print(f"   Tasks: {len(previous_state.get('generated_tasks', []))}")
            print(f"   History: {len(previous_state.get('conversation_history', []))} messages")
            
            state = previous_state.copy()
            state["user_message"] = user_message
            state["next_agent"] = None
            state["response_to_user"] = ""
            # Reset agent messages for this turn (keep history but start fresh for loop detection)
            state["agent_messages"] = []
            # Reset completed agents for this turn
            state["completed_agents"] = []
            
            # Add user message to conversation history
            add_to_conversation_history(state, "user", user_message)
        else:
            # New conversation
            print(f"🆕 Creating new state")
            state = create_initial_state(session_id, user_message)
            # Add user message to conversation history
            add_to_conversation_history(state, "user", user_message)
        
        # Run orchestration
        print(f"\n▶️ Starting orchestration...")
        final_state = self.graph.invoke(state)
        
        # Add agent response to conversation history
        if final_state.get("response_to_user"):
            add_to_conversation_history(
                final_state,
                "agent",
                final_state["response_to_user"],
                {
                    "workflow_type": final_state.get("workflow_type"),
                    "project_name": final_state.get("project_name"),
                    "weekly_goal": final_state.get("weekly_goal"),
                    "tasks_count": len(final_state.get("generated_tasks", []))
                }
            )
        
        # Save final state
        memory.store_state(session_id, final_state)
        print(f"\n💾 Final state saved:")
        print(f"   Project: {final_state.get('project_name')}")
        print(f"   Goal: {final_state.get('weekly_goal')}")
        print(f"   Tasks: {len(final_state.get('generated_tasks', []))}")
        print(f"   History: {len(final_state.get('conversation_history', []))} messages")
        
        # Build response
        response = {
            "success": True,
            "session_id": session_id,
            "workflow_type": final_state.get("workflow_type"),
            "response": final_state.get("response_to_user"),
            "project_name": final_state.get("project_name"),
            "weekly_goal": final_state.get("weekly_goal"),
            "generated_tasks": final_state.get("generated_tasks", []),
            "assignment_plan": final_state.get("assignment_plan"),
            "pending_approval": final_state.get("pending_approval", False),
            "slack_channel_id": final_state.get("slack_channel_id"),
            "trello_board_id": final_state.get("trello_board_id"),
            "agent_messages": final_state.get("agent_messages", []),
            "conversation_history": final_state.get("conversation_history", [])
        }
        
        print(f"\n✅ Response ready: {response['response'][:100] if response['response'] else 'No response'}")
        print(f"{'='*60}\n")
        
        return response


# Global instance
task_orchestrator = TaskOrchestrator()
