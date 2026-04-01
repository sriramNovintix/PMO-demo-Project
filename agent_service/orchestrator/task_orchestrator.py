"""
Non-Deterministic Task Orchestrator
Uses LangGraph for dynamic agent coordination
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
from agents.notification_agent import notification_agent
from agents.status_agent import status_agent
from agents.message_agent import message_agent


class TaskOrchestrator:
    """
    Non-deterministic orchestrator
    Controller agent decides next steps dynamically
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
        workflow.add_node("notification", self._notification_node)
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
                "notification": "notification",
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
        workflow.add_edge("notification", "controller")
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
        """Goal understanding agent"""
        print(f"\n📋 GOAL UNDERSTANDING AGENT")
        print(f"   Current state - Project: {state.get('project_name')}, Goal: {state.get('weekly_goal')}")
        
        existing_context = {
            "project_name": state.get("project_name"),
            "weekly_goal": state.get("weekly_goal")
        }
        
        result = goal_understanding_agent.understand_goal(
            state["user_message"],
            existing_context
        )
        
        if result["success"]:
            # Update state with extracted information - CRITICAL FIX
            extracted_project = result.get("project_name")
            extracted_goal = result.get("weekly_goal")
            
            # Only update if we got new information
            if extracted_project and extracted_project != "None" and extracted_project.lower() != "none":
                state["project_name"] = extracted_project
                print(f"   ✅ Extracted project name: {extracted_project}")
            
            if extracted_goal and extracted_goal != "None" and extracted_goal.lower() != "none":
                state["weekly_goal"] = extracted_goal
                print(f"   ✅ Extracted weekly goal: {extracted_goal}")
            
            # Store in memory immediately
            memory.store_state(state["session_id"], state)
            print(f"   💾 State saved to memory")
            
            add_agent_message(
                state,
                "goal_understanding",
                "controller",
                "Goal extracted successfully",
                {
                    "project_name": state.get("project_name"),
                    "weekly_goal": state.get("weekly_goal"),
                    "extracted_data": result
                }
            )
            
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
        """Task generation agent"""
        print(f"\n📝 TASK GENERATION AGENT")
        
        # Check if we have required information
        if not state.get("weekly_goal"):
            print("   ⚠️ Missing weekly goal")
            add_agent_message(
                state,
                "task_generation",
                "controller",
                "Missing weekly goal - cannot generate tasks"
            )
            mark_agent_completed(state, "task_generation")
            return state
        
        # Use project name or default
        project_name = state.get("project_name") or "Unnamed Project"
        weekly_goal = state.get("weekly_goal")
        
        print(f"   Project: {project_name}")
        print(f"   Goal: {weekly_goal}")
        
        result = task_generation_agent.generate_tasks(
            project_name,
            weekly_goal
        )
        
        if result["success"]:
            state["generated_tasks"] = result["tasks"]
            
            # Save tasks to database immediately
            from database import db
            session_id = state.get("session_id")
            
            for task in result["tasks"]:
                task_data = {
                    "title": task.get("title", "Untitled Task"),
                    "description": task.get("description", ""),
                    "assigned_to": None,  # Not assigned yet
                    "assigned_to_email": None,
                    "estimated_hours": task.get("estimated_hours", 0),
                    "session_id": session_id,
                    "project_id": project_name
                }
                
                db_result = db.create_task(task_data)
                if db_result["success"]:
                    # Store task_id in the task object
                    task["task_id"] = db_result["task_id"]
                    print(f"   ✅ Saved task to DB: {task['title']}")
                else:
                    print(f"   ⚠️ Failed to save task: {db_result.get('error')}")
            
            add_agent_message(
                state,
                "task_generation",
                "controller",
                f"Generated {len(result['tasks'])} tasks",
                {"tasks": result["tasks"], "total_hours": result["total_estimated_hours"]}
            )
            
            print(f"   Generated {len(result['tasks'])} tasks")
            print(f"   Total hours: {result['total_estimated_hours']}")
        else:
            add_agent_message(
                state,
                "task_generation",
                "controller",
                f"Error: {result.get('error')}"
            )
        
        mark_agent_completed(state, "task_generation")
        return state
    
    def _skill_matching_node(self, state: AgentState) -> AgentState:
        """Skill matching agent"""
        print(f"\n🎯 SKILL MATCHING AGENT")
        
        if not state.get("generated_tasks") or not state.get("employees"):
            add_agent_message(
                state,
                "skill_matching",
                "controller",
                "Missing tasks or employee information"
            )
            return state
        
        result = skill_matching_agent.match_skills(
            state["generated_tasks"],
            state["employees"]
        )
        
        if result["success"]:
            # Store skill matches in state for allocation agent
            state["skill_matches"] = result["task_matches"]
            
            add_agent_message(
                state,
                "skill_matching",
                "controller",
                "Skill matching completed",
                {"task_matches": result["task_matches"]}
            )
            
            print(f"   Matched {len(result['task_matches'])} tasks")
        else:
            add_agent_message(
                state,
                "skill_matching",
                "controller",
                f"Error: {result.get('error')}"
            )
        
        mark_agent_completed(state, "skill_matching")
        return state
    
    def _task_allocation_node(self, state: AgentState) -> AgentState:
        """Task allocation agent"""
        print(f"\n📊 TASK ALLOCATION AGENT")
        
        if not state.get("skill_matches"):
            add_agent_message(
                state,
                "task_allocation",
                "controller",
                "Missing skill matching results"
            )
            return state
        
        result = task_allocation_agent.allocate_tasks(state["skill_matches"])
        
        if result["success"]:
            state["assignment_plan"] = result
            state["pending_approval"] = True
            
            add_agent_message(
                state,
                "task_allocation",
                "controller",
                "Allocation plan created - pending approval",
                result
            )
            
            print(f"   Created allocation for {len(result['assignments'])} employees")
            print(f"   Unassigned tasks: {len(result.get('unassigned_tasks', []))}")
        else:
            add_agent_message(
                state,
                "task_allocation",
                "controller",
                f"Error: {result.get('error')}"
            )
        
        mark_agent_completed(state, "task_allocation")
        return state
    
    def _notification_node(self, state: AgentState) -> AgentState:
        """Notification agent"""
        print(f"\n📢 NOTIFICATION AGENT")
        
        # Check if creating project workspace
        if state.get("workflow_type") == "CREATE_PROJECT" and not state.get("slack_channel_id"):
            result = notification_agent.create_project_workspace(
                state["project_name"],
                state.get("weekly_goal", "")
            )
            
            if result["success"]:
                state["slack_channel_id"] = result["slack_channel_id"]
                state["trello_board_id"] = result["trello_board_id"]
                
                # Store project in memory
                memory.store_project(state["project_name"], {
                    "project_name": state["project_name"],
                    "slack_channel_id": result["slack_channel_id"],
                    "trello_board_id": result["trello_board_id"],
                    "weekly_goal": state.get("weekly_goal")
                })
                
                add_agent_message(
                    state,
                    "notification",
                    "controller",
                    "Project workspace created",
                    result
                )
                
                print(f"   Slack channel: {result['slack_channel_id']}")
                print(f"   Trello board: {result['trello_board_id']}")
            else:
                add_agent_message(
                    state,
                    "notification",
                    "controller",
                    f"Errors: {result['errors']}"
                )
        
        # Check if executing approved assignments
        elif state.get("approved") and state.get("assignment_plan"):
            # Get employee data from memory
            from memory.session_memory import memory
            employees_data = memory.get_all_employees()
            
            result = notification_agent.execute_assignments(
                state.get("trello_board_id", ""),
                state["assignment_plan"],
                employees_data,
                session_id=state["session_id"],
                project_id=state.get("project_name")
            )
            
            add_agent_message(
                state,
                "notification",
                "controller",
                "Assignments executed" if result["success"] else f"Errors: {result['errors']}",
                result
            )
            
            print(f"   Execution: {'Success' if result['success'] else 'Failed'}")
        
        mark_agent_completed(state, "notification")
        return state
    
    def _status_node(self, state: AgentState) -> AgentState:
        """Status agent"""
        print(f"\n📊 STATUS AGENT")
        
        result = status_agent.get_status_update()
        
        if result["success"]:
            state["response_to_user"] = result["status_message"]
            
            add_agent_message(
                state,
                "status",
                "controller",
                "Status retrieved",
                result
            )
            
            print(f"   Status for {len(result.get('employee_status', []))} employees")
        else:
            state["response_to_user"] = result["status_message"]
            add_agent_message(
                state,
                "status",
                "controller",
                f"Error: {result.get('error')}"
            )
        
        mark_agent_completed(state, "status")
        return state
    
    def _message_node(self, state: AgentState) -> AgentState:
        """Message agent"""
        print(f"\n💬 MESSAGE AGENT")
        
        workflow_type = state.get("workflow_type")
        
        if workflow_type == "SEND_STATUS":
            # Send status report to Slack
            result = message_agent.send_status_report()
            
            if result["success"]:
                state["response_to_user"] = f"Status report sent to Slack #{result['channel']}"
            else:
                state["response_to_user"] = result["message"]
            
            add_agent_message(
                state,
                "message",
                "controller",
                result["message"],
                result
            )
            
            print(f"   Status report sent: {result['success']}")
        
        elif workflow_type == "SEND_MESSAGE":
            # Extract message from user input
            user_message = state.get("user_message", "")
            
            # Simple extraction - everything after "send message" or similar
            message_to_send = user_message
            if "send message" in user_message.lower():
                parts = user_message.lower().split("send message")
                if len(parts) > 1:
                    message_to_send = parts[1].strip()
            elif "send" in user_message.lower():
                parts = user_message.lower().split("send")
                if len(parts) > 1:
                    message_to_send = parts[1].strip()
            
            if not message_to_send or message_to_send == user_message:
                state["response_to_user"] = "What message would you like to send to Slack?"
                state["awaiting_message"] = True
            else:
                result = message_agent.send_custom_message(message_to_send)
                
                if result["success"]:
                    state["response_to_user"] = f"Message sent to Slack #{result['channel']}"
                else:
                    state["response_to_user"] = result["message"]
                
                add_agent_message(
                    state,
                    "message",
                    "controller",
                    result["message"],
                    result
                )
                
                print(f"   Message sent: {result['success']}")
        
        mark_agent_completed(state, "message")
        return state
    
    def _human_approval_node(self, state: AgentState) -> AgentState:
        """Human approval checkpoint"""
        print(f"\n👤 HUMAN APPROVAL REQUIRED")
        
        if state.get("pending_approval") and state.get("assignment_plan"):
            # Send approval request
            if state.get("slack_channel_id"):
                notification_agent.send_approval_request(
                    state["slack_channel_id"],
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
            
            # Add task information if tasks were generated
            if state.get("generated_tasks"):
                tasks = state["generated_tasks"]
                response += f"\n✅ Generated {len(tasks)} tasks:\n\n"
                for i, task in enumerate(tasks, 1):  # Show all tasks
                    title = task.get('title', 'Untitled')
                    hours = task.get('estimated_hours', 0)
                    priority = task.get('priority', 'medium')
                    skills = ', '.join(task.get('required_skills', [])[:3])
                    response += f"{i}. {title}\n"
                    response += f"   • Duration: {hours}h | Priority: {priority}\n"
                    if skills:
                        response += f"   • Skills: {skills}\n"
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
