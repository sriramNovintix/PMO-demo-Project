"""
Configuration for Task Orchestrator
"""
import os
import json
import re
import boto3
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # AWS Bedrock
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    MODEL_ID = os.getenv("MODEL_ID", "us.meta.llama3-3-70b-instruct-v1:0")
    
    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://srirampractice_db_user:XeNXvqRyesHBvEge@cluster-aihr.qbbzict.mongodb.net/")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "task_orchestrator")
    
    # API Keys
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    TRELLO_API_KEY = os.getenv("TRELLO_API_KEY", "")
    TRELLO_TOKEN = os.getenv("TRELLO_TOKEN", "")
    
    # AgentOps
    AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY", "")
    
    # Server
    HOST = "0.0.0.0"
    PORT = 8000


# Initialize Bedrock client
bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name=Config.AWS_REGION,
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
)


class BedrockLLM:
    """Bedrock LLM wrapper compatible with LangChain interface"""
    
    def __init__(self, client, model_id):
        self.client = client
        self.model_id = model_id
    
    def __or__(self, other):
        """Support pipe operator for LangChain chains"""
        # Return a chain that combines prompt and LLM
        return LangChainChain(other, self)
    
    def invoke(self, input_data):
        """Invoke Bedrock model with messages"""
        # Handle different input formats
        if isinstance(input_data, dict):
            # Extract all values and create prompt
            prompt_parts = []
            for key, value in input_data.items():
                if value and value != "None":
                    prompt_parts.append(f"{key}: {value}")
            prompt = "\n".join(prompt_parts)
        elif isinstance(input_data, list):
            # List of messages
            prompt = "\n".join([str(m.content if hasattr(m, 'content') else m) for m in input_data])
        else:
            prompt = str(input_data)
        
        payload = {
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant. Return valid JSON when requested."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )
        
        raw_body = response["body"].read()
        if not raw_body:
            raise ValueError("Empty response from Bedrock")
        
        try:
            result = json.loads(raw_body)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from Bedrock: {raw_body}")
        
        # Handle different response formats
        if "output" in result:
            content_list = result["output"]["message"]["content"]
            if isinstance(content_list, list) and len(content_list) > 0:
                content = content_list[0].get("text", "")
            else:
                content = str(content_list)
        elif "choices" in result:
            content = result["choices"][0]["message"]["content"]
        else:
            raise ValueError(f"Unknown Bedrock response format: {result}")
        
        # Strip reasoning tags
        content = re.sub(r"<reasoning>.*?</reasoning>", "", content, flags=re.DOTALL).strip()
        
        # Return response object compatible with LangChain
        return type("LLMResponse", (), {"content": content})()


class LangChainChain:
    """Simple chain implementation for LangChain compatibility"""
    
    def __init__(self, prompt, llm):
        self.prompt = prompt
        self.llm = llm
    
    def invoke(self, input_data):
        """Execute the chain"""
        # Format prompt with input data
        if hasattr(self.prompt, 'format_messages'):
            messages = self.prompt.format_messages(**input_data)
            formatted_input = "\n".join([m.content for m in messages])
        else:
            formatted_input = input_data
        
        # Call LLM
        return self.llm.invoke(formatted_input)


def get_llm():
    """Get LLM instance"""
    return BedrockLLM(bedrock_client, Config.MODEL_ID)


def invoke_with_prompt(prompt_template, llm, **kwargs):
    """Helper to invoke LLM with prompt template"""
    messages = prompt_template.format_messages(**kwargs)
    prompt_text = "\n".join([m.content for m in messages])
    return llm.invoke(prompt_text)
