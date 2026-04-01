# TaskFlow - AI-Powered Task Management System

An intelligent task orchestration system with AI agents, Kanban board, and Slack integration.

## Features

- 🤖 AI-powered task generation from goals
- 📋 Kanban board with drag-and-drop
- 👥 Candidate management with resume parsing
- 🎯 Smart task allocation based on skills
- 💬 Conversation history with context management
- 📊 Real-time status tracking
- 🔔 Slack notifications
- 📈 AgentOps monitoring (optional) - Track agent performance, LLM calls, and costs

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- MongoDB Atlas account
- AWS Bedrock access (for AI)
- AgentOps API key (optional, for monitoring)

### 1. Backend Setup

```bash
cd task-orchestrator/agent_service

# Install dependencies
pip install -r requirements.txt

# Configure .env file
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
MODEL_ID=us.meta.llama3-3-70b-instruct-v1:0
MONGODB_URI=your_mongodb_uri
MONGODB_DB_NAME=task_orchestrator
SLACK_BOT_TOKEN=your_slack_token (optional)
AGENTOPS_API_KEY=your_agentops_key (optional)

# Start backend
python main.py
```

Backend runs at: http://localhost:8000

### 2. Frontend Setup

```bash
cd task-orchestrator/web_app

# Install dependencies
npm install

# Start frontend
npm run dev
```

Frontend runs at: http://localhost:3000

## How to Use

### 1. Set a Goal
```
"project name: recruitment software
goal: create a login page"
```
AI generates tasks automatically.

### 2. View Tasks
Navigate to `/tasks` to see Kanban board with:
- To Do
- In Progress  
- Completed

Drag tasks between columns to update status.

### 3. Upload Resumes
Click the 📎 icon to upload candidate resumes (PDF).
AI extracts skills and experience automatically.

### 4. Assign Tasks
```
"assign tasks to john"
```
AI matches tasks to employee skills and creates allocation plan.

### 5. Check Status
```
"show status"
```
See task progress for all employees.

## Project Structure

```
task-orchestrator/
├── agent_service/          # Backend (Python/FastAPI)
│   ├── agents/            # AI agents (goal, task, skill matching)
│   ├── orchestrator/      # Agent coordination
│   ├── tools/             # Slack, Trello integrations
│   ├── database.py        # MongoDB operations
│   └── main.py            # API server
│
└── web_app/               # Frontend (Next.js/React)
    ├── app/               # Pages (dashboard, tasks, candidates)
    ├── components/        # UI components (Sidebar, etc.)
    └── public/            # Static assets
```

## Key Technologies

**Backend:**
- FastAPI - REST API
- LangGraph - Agent orchestration
- AWS Bedrock - AI/LLM
- MongoDB - Data persistence
- PyPDF2 - Resume parsing

**Frontend:**
- Next.js 14 - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- Axios - API calls

## API Endpoints

- `POST /chat` - Send message to AI
- `GET /tasks` - Get all tasks
- `POST /tasks/{id}/status` - Update task status
- `GET /candidates` - Get candidates
- `POST /candidates/upload` - Upload resume
- `GET /employees` - Get employees
- `GET /sessions` - Get all sessions
- `GET /session/{id}` - Get session details

## Features in Detail

### AI Agents
- **Goal Understanding** - Extracts project goals
- **Task Generation** - Creates actionable tasks
- **Skill Matching** - Matches tasks to employee skills
- **Task Allocation** - Creates optimal work distribution
- **Status Agent** - Provides progress updates
- **Message Agent** - Handles Slack communication

### Conversation History
- Stores last 20 messages per session
- Context window management
- Persists across page refreshes
- Loads from MongoDB automatically

### Task Management
- Create tasks from goals
- Assign to employees
- Track status (todo/in progress/completed)
- Filter by employee or unassigned
- Drag-and-drop status updates
- Slack notifications on changes

### Candidate Management
- Upload PDF resumes
- AI extracts name, email, skills, experience
- Store in MongoDB
- Select/reject candidates
- Convert to employees

## Troubleshooting

### Backend won't start
- Check MongoDB URI in `.env`
- Verify AWS credentials
- Install all requirements: `pip install -r requirements.txt`

### Frontend won't start
- Delete `node_modules` and `.next`
- Run `npm install` again
- Check Node.js version (18+)

### Tasks not showing
- Check MongoDB connection
- Verify backend is running
- Check browser console for errors
- Test: `curl http://localhost:8000/tasks`

### Sessions duplicating
- Clear localStorage: `localStorage.clear()`
- Refresh page
- Check `current_session_id` in localStorage

## Debug Endpoints

- `GET /debug/database` - Check database connection and data
- `GET /health` - Health check

## Configuration

### Change Context Window
Edit `agent_service/state.py`:
```python
add_to_conversation_history(state, role, content, max_history=20)
```

### Change AI Model
Edit `agent_service/.env`:
```
MODEL_ID=your_model_id
```

### Enable AgentOps Monitoring
1. Sign up at https://agentops.ai
2. Get your API key
3. Add to `.env`:
```
AGENTOPS_API_KEY=your_api_key
```
4. Restart backend
5. View metrics at https://app.agentops.ai

AgentOps tracks:
- Agent execution sessions
- LLM calls and token usage
- Operation performance
- Error rates
- Cost analysis

## License

MIT

## Support

For issues or questions, check:
1. Backend logs for errors
2. Browser console for frontend errors
3. MongoDB connection status
4. API endpoint responses
