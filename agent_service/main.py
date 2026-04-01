"""
Task Orchestrator - Agent Service
FastAPI application with database persistence and candidate management
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from orchestrator.task_orchestrator import task_orchestrator
from memory.session_memory import memory
from database import db
from resume_parser import resume_parser
from datetime import datetime
import PyPDF2
import io
import agentops
from config import Config

# Initialize AgentOps if API key is provided
if Config.AGENTOPS_API_KEY:
    agentops.init(
        api_key=Config.AGENTOPS_API_KEY,
        default_tags=["task-orchestrator", "production"],
        auto_start_session=False
    )
    print("✅ AgentOps initialized")
else:
    print("⚠️  AgentOps API key not found - tracking disabled")

app = FastAPI(
    title="Task Orchestrator - Agent Service",
    description="Non-deterministic multi-agent work allocation system with database persistence",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Models
class ChatRequest(BaseModel):
    """Chat request model"""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="User message")


class CandidateRequest(BaseModel):
    """Add candidate request"""
    name: str = Field(..., description="Candidate name")
    email: str = Field(..., description="Candidate email")
    skills: List[str] = Field(..., description="Candidate skills")
    capacity_hours: Optional[int] = Field(40, description="Weekly capacity in hours")


class EmployeeRequest(BaseModel):
    """Add employee request"""
    name: str = Field(..., description="Employee name")
    email: str = Field(..., description="Employee email")
    skills: List[str] = Field(..., description="Employee skills")
    capacity_hours: Optional[int] = Field(40, description="Weekly capacity in hours")


class ApprovalRequest(BaseModel):
    """Approval request"""
    session_id: str = Field(..., description="Session identifier")
    approved: bool = Field(..., description="Approval status")


# Chat Endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint - processes user messages through orchestrator
    
    The controller agent analyzes the message and dynamically decides next steps
    """
    # Start AgentOps session for this chat interaction
    agentops_session = None
    if Config.AGENTOPS_API_KEY:
        agentops_session = agentops.start_session(
            tags=["chat", request.session_id[:8], "user-interaction"]
        )
    
    try:
        print(f"\n{'='*60}")
        print(f"📨 INCOMING REQUEST")
        print(f"   Session ID: {request.session_id}")
        print(f"   Message: {request.message}")
        print(f"{'='*60}\n")
        
        result = task_orchestrator.process_message(
            session_id=request.session_id,
            user_message=request.message
        )
        
        print(f"\n{'='*60}")
        print(f"✅ RESPONSE READY")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Workflow: {result.get('workflow_type', 'N/A')}")
        print(f"{'='*60}\n")
        
        # End AgentOps session successfully
        if agentops_session:
            agentops.end_session("Success")
        
        return result
    
    except Exception as e:
        # End AgentOps session with error
        if agentops_session:
            agentops.end_session("Fail")
        
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )
        return result
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        print(f"\n{'='*60}")
        print(f"❌ ERROR IN CHAT ENDPOINT")
        print(f"   Error: {str(e)}")
        print(f"   Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "session_id": request.session_id,
                "traceback": error_trace
            }
        )


# Candidate Endpoints
@app.post("/candidates/upload")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and parse resume
    
    Accepts PDF files and extracts candidate information
    """
    try:
        print(f"\n{'='*60}")
        print(f"📄 RESUME UPLOAD")
        print(f"   Filename: {file.filename}")
        print(f"{'='*60}\n")
        
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Read PDF content
        print("Reading PDF content...")
        content = await file.read()
        print(f"PDF size: {len(content)} bytes")
        
        # Import PyPDF2
        try:
            import PyPDF2
            import io
        except ImportError as e:
            print(f"❌ PyPDF2 not installed: {e}")
            raise HTTPException(
                status_code=500,
                detail="PyPDF2 library not installed. Run: pip install PyPDF2"
            )
        
        # Parse PDF
        print("Parsing PDF...")
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            print(f"PDF has {len(pdf_reader.pages)} pages")
        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Could not read PDF file: {str(e)}"
            )
        
        # Extract text from all pages
        resume_text = ""
        for i, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                resume_text += page_text
                print(f"Page {i+1}: {len(page_text)} characters")
            except Exception as e:
                print(f"Warning: Could not extract text from page {i+1}: {e}")
        
        if not resume_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. The PDF might be image-based or encrypted."
            )
        
        print(f"Total extracted text: {len(resume_text)} characters")
        
        # Parse resume with LLM
        print("Parsing resume with AI...")
        try:
            parsed_data = resume_parser.parse_resume(resume_text)
            print(f"✅ Resume parsed successfully")
            print(f"   Name: {parsed_data.get('candidate_name')}")
            print(f"   Email: {parsed_data.get('email')}")
            print(f"   Skills: {len(parsed_data.get('skills_with_context', []))}")
        except Exception as e:
            print(f"❌ Error parsing resume with AI: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: Create basic candidate data
            print("Using fallback: creating basic candidate data")
            parsed_data = {
                "candidate_name": "Unknown Candidate",
                "email": None,
                "total_experience_years": 0,
                "skills_with_context": [],
                "raw_text": resume_text[:500]  # Store first 500 chars
            }
            print("⚠️ Resume parsing failed, using fallback data")
        
        # Extract skills list
        skills = []
        if parsed_data.get("skills_with_context"):
            skills = [s["skill"] for s in parsed_data["skills_with_context"]]
        
        # Prepare candidate data
        candidate_data = {
            "name": parsed_data.get("candidate_name", "Unknown"),
            "email": parsed_data.get("email"),
            "skills": skills,
            "experience_years": parsed_data.get("total_experience_years", 0),
            "resume_data": parsed_data
        }
        
        # Add to database
        print("Saving to database...")
        result = db.add_candidate(candidate_data)
        
        if result["success"]:
            print(f"✅ Candidate saved: {result['candidate_id']}")
            return {
                "success": True,
                "message": "Resume uploaded and parsed successfully",
                "candidate_id": result["candidate_id"],
                "candidate": {
                    **candidate_data,
                    "candidate_id": result["candidate_id"],
                    "status": "pending"
                }
            }
        else:
            print(f"❌ Database error: {result['error']}")
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n{'='*60}")
        print(f"❌ UNEXPECTED ERROR IN UPLOAD")
        print(f"   Error: {str(e)}")
        print(f"   Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "traceback": error_trace}
        )


@app.post("/candidates/add")
async def add_candidate(request: CandidateRequest):
    """
    Add candidate to the system
    
    Candidates are pending and need to be selected or rejected
    """
    try:
        candidate_data = {
            "name": request.name,
            "email": request.email,
            "skills": request.skills,
            "capacity_hours": request.capacity_hours
        }
        
        result = db.add_candidate(candidate_data)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "candidate_id": result["candidate_id"],
                "candidate": {
                    **candidate_data,
                    "candidate_id": result["candidate_id"],
                    "status": "pending"
                }
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@app.get("/candidates")
async def get_candidates():
    """Get all candidates"""
    try:
        candidates = db.get_all_candidates()
        return {
            "success": True,
            "candidates": candidates,
            "count": len(candidates)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@app.get("/candidates/search")
async def search_candidates(skills: str = ""):
    """
    Search candidates by skills
    
    Args:
        skills: Comma-separated list of skills to search for
    
    Returns:
        List of matching candidates with match scores
    """
    try:
        all_candidates = db.get_all_candidates()
        
        if not skills:
            return {
                "success": True,
                "candidates": all_candidates,
                "count": len(all_candidates)
            }
        
        # Parse skills
        search_skills = [s.strip().lower() for s in skills.split(",")]
        
        # Calculate match scores
        matched_candidates = []
        for candidate in all_candidates:
            candidate_skills = [s.lower() for s in candidate.get("skills", [])]
            
            # Calculate match
            matching_skills = [s for s in search_skills if s in candidate_skills]
            match_score = len(matching_skills) / len(search_skills) if search_skills else 0
            
            if match_score > 0:
                matched_candidates.append({
                    **candidate,
                    "match_score": match_score,
                    "matching_skills": matching_skills,
                    "missing_skills": [s for s in search_skills if s not in candidate_skills]
                })
        
        # Sort by match score
        matched_candidates.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "success": True,
            "candidates": matched_candidates,
            "count": len(matched_candidates),
            "search_skills": search_skills
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@app.post("/candidates/{candidate_id}/select")
async def select_candidate(candidate_id: str):
    """
    Select candidate - move to employees
    
    This removes the candidate and creates an employee record
    """
    try:
        result = db.select_candidate(candidate_id)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "employee_id": result["employee_id"]
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=result["error"]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@app.post("/candidates/{candidate_id}/reject")
async def reject_candidate(candidate_id: str):
    """
    Reject candidate - delete from database
    
    This permanently removes the candidate
    """
    try:
        result = db.reject_candidate(candidate_id)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=result["error"]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


# Employee Endpoints
@app.post("/employees/add")
async def add_employee(request: EmployeeRequest):
    """
    Add employee directly to the system
    
    Stores employee information for skill matching and task allocation
    """
    try:
        employee_data = {
            "name": request.name,
            "email": request.email,
            "skills": request.skills,
            "capacity_hours": request.capacity_hours
        }
        
        result = db.add_employee(employee_data)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "employee_id": result["employee_id"],
                "employee": {
                    **employee_data,
                    "employee_id": result["employee_id"]
                }
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@app.get("/employees")
async def get_employees():
    """Get all employees from database"""
    try:
        employees = db.get_all_employees()
        return {
            "success": True,
            "employees": employees,
            "count": len(employees)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


# Task Endpoints
@app.get("/tasks")
async def get_tasks(session_id: str = None, status: str = None):
    """
    Get all tasks, optionally filtered by session or status
    
    Args:
        session_id: Optional session ID filter
        status: Optional status filter (todo, in_progress, completed)
    """
    try:
        if status:
            tasks = db.get_tasks_by_status(status, session_id)
        else:
            tasks = db.get_all_tasks(session_id)
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@app.post("/tasks/{task_id}/status")
async def update_task_status(task_id: str, status: str):
    """
    Update task status
    
    Args:
        task_id: Task ID
        status: New status (todo, in_progress, completed)
    """
    try:
        if status not in ["todo", "in_progress", "completed"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Must be: todo, in_progress, or completed"
            )
        
        result = db.update_task_status(task_id, status)
        
        if result["success"]:
            # Send Slack notification
            task = result["task"]
            status_emoji = {
                "todo": "📋",
                "in_progress": "🔄",
                "completed": "✅"
            }
            
            message = f"""{status_emoji[status]} *Task Status Updated*

*Task:* {task['title']}
*Assigned to:* {task.get('assigned_to', 'Unassigned')}
*New Status:* {status.replace('_', ' ').title()}
*Updated:* {task['updated_at']}"""
            
            from tools.slack_tools import slack_tools
            slack_tools.send_message_to_channel(
                channel_name="demo-projects",
                message=message
            )
            
            return result
        else:
            raise HTTPException(
                status_code=404,
                detail=result["error"]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@app.post("/tasks/{task_id}/assign")
async def assign_task_to_employee(task_id: str, employee_name: str):
    """
    Manually assign task to employee with skill validation
    
    Args:
        task_id: Task ID
        employee_name: Employee name to assign to
    """
    try:
        # Get task
        tasks = db.get_all_tasks()
        task = next((t for t in tasks if t['task_id'] == task_id), None)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get employee
        employees = db.get_all_employees()
        employee = next((e for e in employees if e['name'] == employee_name), None)
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Validate skills (at least some overlap)
        task_title_lower = task['title'].lower()
        employee_skills_lower = [s.lower() for s in employee.get('skills', [])]
        
        # Check if any employee skill is mentioned in task title
        has_relevant_skill = any(skill in task_title_lower for skill in employee_skills_lower)
        
        if not has_relevant_skill:
            # Check if task mentions any technical terms that might match
            common_tech_terms = ['api', 'database', 'frontend', 'backend', 'test', 'deploy', 'design', 'auth']
            has_general_match = any(term in task_title_lower for term in common_tech_terms)
            
            if not has_general_match:
                return {
                    "success": False,
                    "message": f"Warning: {employee_name} may not have relevant skills for this task. Task requires different expertise.",
                    "assigned": False
                }
        
        # Update task assignment using db.update_task_assignment
        now = datetime.now().isoformat()
        update_result = db.tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "assigned_to": employee_name,
                    "assigned_to_email": employee.get('email'),
                    "updated_at": now
                }
            }
        )
        
        if update_result.modified_count > 0:
            # Send Slack notification
            from tools.slack_tools import slack_tools
            message = f"""📌 *Task Manually Assigned*

*Task:* {task['title']}
*Assigned to:* {employee_name}
*Email:* {employee.get('email')}
*Estimated Hours:* {task['estimated_hours']}h

Task has been assigned successfully!"""
            
            slack_tools.send_message_to_channel(
                channel_name="demo-projects",
                message=message
            )
            
            return {
                "success": True,
                "message": f"Task assigned to {employee_name}",
                "assigned": True
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to assign task")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@app.get("/status")
async def get_employee_status():
    """Get status summary for all employees"""
    try:
        status_list = db.get_employee_status()
        return {
            "success": True,
            "employees": status_list,
            "count": len(status_list)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@app.delete("/employees/{employee_id}")
async def delete_employee(employee_id: str):
    """
    Delete employee from database
    
    This permanently removes the employee
    """
    try:
        result = db.delete_employee(employee_id)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=result["error"]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


# Approval Endpoint
@app.post("/approval")
async def submit_approval(request: ApprovalRequest):
    """
    Submit approval for pending task assignments
    
    If approved, the notification agent will create Trello cards and send Slack notifications
    """
    try:
        # Get latest state
        state = memory.get_latest_state(request.session_id)
        
        if not state:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        if not state.get("pending_approval"):
            return {
                "success": False,
                "message": "No pending approval for this session"
            }
        
        # Update state with approval
        state["approved"] = request.approved
        state["pending_approval"] = False
        
        if request.approved:
            # Process approval - trigger notification agent
            state["user_message"] = "Execute approved task assignments"
            state["next_agent"] = None
            state["completed_agents"] = []
            
            result = task_orchestrator.process_message(
                session_id=request.session_id,
                user_message="Execute approved task assignments"
            )
            
            return {
                "success": True,
                "message": "Assignments approved and executed",
                "result": result
            }
        else:
            memory.store_state(request.session_id, state)
            memory.clear_pending_approvals(request.session_id)
            
            return {
                "success": True,
                "message": "Assignments rejected"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


# Session Endpoints
@app.get("/sessions")
async def get_all_sessions():
    """Get all sessions from database"""
    try:
        sessions = db.get_all_sessions()
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all associated data from database"""
    try:
        result = db.delete_session(session_id)
        if result["success"]:
            return {"success": True, "message": result["message"]}
        else:
            raise HTTPException(status_code=404, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session state from database"""
    try:
        state = memory.get_latest_state(session_id)
        
        if not state:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        return {
            "success": True,
            "session": state
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "task-orchestrator-agent-service",
        "version": "2.0.0",
        "features": [
            "database_persistence",
            "candidate_management",
            "employee_management",
            "session_storage"
        ]
    }


# Debug endpoint
@app.get("/debug/database")
async def debug_database():
    """Debug endpoint to check database connection and data"""
    try:
        # Test MongoDB connection
        tasks = db.get_all_tasks()
        sessions = db.get_all_sessions()
        employees = db.get_all_employees()
        candidates = db.get_all_candidates()
        
        return {
            "success": True,
            "database": "MongoDB",
            "connection": "OK",
            "collections": {
                "tasks": {
                    "count": len(tasks),
                    "sample": tasks[:2] if tasks else []
                },
                "sessions": {
                    "count": len(sessions),
                    "sample": sessions[:2] if sessions else []
                },
                "employees": {
                    "count": len(employees),
                    "sample": employees[:2] if employees else []
                },
                "candidates": {
                    "count": len(candidates),
                    "sample": candidates[:2] if candidates else []
                }
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": __import__('traceback').format_exc()
        }


if __name__ == "__main__":
    import uvicorn
    from config import Config
    
    print("🚀 Starting Task Orchestrator Agent Service v2.0")
    print(f"   Port: {Config.PORT}")
    print(f"   Model: {Config.MODEL_ID}")
    print(f"   Database: MongoDB ({Config.MONGODB_DB_NAME})")
    print(f"   Features: Candidate Management, Database Persistence, Task Management")
    
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT
    )
