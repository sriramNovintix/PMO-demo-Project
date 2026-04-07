"""
Configuration - Environment-driven settings
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration from environment variables"""
    
    # MongoDB (from .env)
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "task_orchestrator")
    
    # Slack (from .env)
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    
    # Gemini API (from .env)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # AgentOps (from .env)
    AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")
    
    # Server
    HOST = "0.0.0.0"
    PORT = 8000


def get_llm():
    """Get LLM instance (Gemini)"""
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        max_tokens=4000,
        google_api_key=Config.GEMINI_API_KEY
    )


def invoke_with_prompt(prompt_template, llm, **kwargs):
    """Helper to invoke LLM with prompt template"""
    messages = prompt_template.format_messages(**kwargs)
    return llm.invoke(messages)
