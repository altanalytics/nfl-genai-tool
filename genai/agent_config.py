"""
Shared agent configuration for the GenAI application.
This module provides a centralized way to configure and create agents
to avoid code duplication between CLI and other components.
"""

import os
import boto3
from strands import Agent
from strands.models import BedrockModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.session.s3_session_manager import S3SessionManager
from strands_tools import shell, editor, python_repl, calculator
import tools.get_schedules as get_schedules
import tools.get_context as get_context
import tools.get_game_inputs as get_game_inputs
import tools.get_game_outputs as get_game_outputs
import tools.nfl_kb_search as nfl_kb_search
import tools.query_athena as query_athena
import tools.nfl_game_service as nfl_game_service

def load_prompt_from_file(filename: str) -> str:
    """
    Load a prompt from a file in the prompts directory.
    
    Args:
        filename: Name of the file (without .md extension)
        
    Returns:
        str: Content of the prompt file
    """
    try:
        prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts')
        file_path = os.path.join(prompts_dir, f"{filename}.md")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return f"Prompt file '{filename}.md' not found"
    except Exception as e:
        return f"Error loading prompt file '{filename}.md': {str(e)}"

def get_system_prompt(personality: str, model: str = 'us.amazon.nova-micro-v1:0') -> str:
    """
    Get the system prompt for a given personality, including rules.
    
    Args:
        personality: Either 'nfl_game_recap', 'nfl_analyst', 'nfl_native_analyst', or custom prompt
        model: The model ID being used
        
    Returns:
        str: Complete system prompt with rules appended
    """
    # Load rules that apply to all prompts
    rules = load_prompt_from_file('rules')
    
    # Handle specific personalities
    if personality in ['nfl_game_recap', 'nfl_analyst', 'nfl_native_analyst']:
        if personality == 'nfl_analyst':
            base_prompt = load_prompt_from_file('nfl_analyst')
        elif personality == 'nfl_native_analyst':
            base_prompt = load_prompt_from_file('nfl_native_analyst')
        else:
            base_prompt = load_prompt_from_file('nfl_tools')
    else:
        # Treat as custom system prompt
        base_prompt = personality
    
    # Replace model placeholder with actual model name
    base_prompt = base_prompt.replace('[current model name]', model)
    
    # Combine base prompt with rules
    return f"{base_prompt}\n\n{rules}"

def create_strands_agent(model = 'us.amazon.nova-pro-v1:0',
                         personality = 'nfl_analyst',
                         session_id = None,
                         s3_bucket = None,
                         s3_prefix = None,
                         tools = None):
    """
    Create and return a configured Strands agent instance.
    
    Model Examples:
    - us.amazon.nova-micro-v1:0
    - us.amazon.nova-premier-v1:0
    - us.amazon.nova-pro-v1:0
    - us.anthropic.claude-3-5-haiku-20241022-v1:0
    - us.anthropic.claude-sonnet-4-20250514-v1:0
    
    Args:
        model (str): The Bedrock model ID to use
        personality (str): Either 'nfl_game_recap', 'nfl_analyst', 'nfl_native_analyst', or custom system prompt
        session_id (str): Session ID for S3 session management
        s3_bucket (str): S3 bucket for session storage
        s3_prefix (str): S3 prefix for session storage
        tools (list): Optional list of tools to use (for MCP integration)
        
    Returns:
        Agent: Configured agent ready for use
    """
    
    # Configure the Bedrock model (simplified like PE)
    bedrock_model = BedrockModel(
        inference_profile_id=model,
        max_tokens=5000,
        temperature=0.7,
        top_p=0.8,
    )

    # Configure conversation management for production
    conversation_manager = SlidingWindowConversationManager(
        window_size=10,  # Limit history size
    )

    # Get the system prompt based on personality
    system_prompt = get_system_prompt(personality, model)
    
    print(f"Received personality parameter: '{personality}'")

    # Create and return the agent (simplified like PE)
    if tools is not None:
        # Use provided tools (e.g., from MCP client)
        print(f"Using provided MCP tools: {[getattr(tool, 'tool_name', str(tool)) for tool in tools]}")
        tools_list = tools
    else:
        # Use local tools based on personality
        if personality == 'nfl_native_analyst':
            print("Using native analyst tools: query_athena, nfl_game_service, nfl_kb_search")
            tools_list = [query_athena, nfl_game_service, nfl_kb_search]
        else:
            print("Using local NFL tools")
            tools_list = [get_schedules, get_context, get_game_inputs, get_game_outputs]
            
            # Add knowledge base tool for nfl_game_recap personality
            if personality == 'nfl_game_recap':
                tools_list.append(nfl_kb_search)

    # Create session manager based on whether S3 parameters are provided
    session_manager = None
    if session_id and s3_bucket and s3_prefix:
        print(f"Creating S3SessionManager - Session: {session_id}, Bucket: {s3_bucket}, Prefix: {s3_prefix}")
        
        # Create boto3 session for better credential handling
        boto_session = boto3.Session(region_name="us-east-1")
        
        session_manager = S3SessionManager(
            session_id=session_id,
            bucket=s3_bucket,
            prefix=s3_prefix,
            boto_session=boto_session,
            region_name="us-east-1"
        )
    else:
        print("Using default SlidingWindowConversationManager (no S3 session persistence)")

    # Create and return the agent
    strands_agent = Agent(
        model=bedrock_model,
        system_prompt=system_prompt,
        conversation_manager=conversation_manager,
        session_manager=session_manager,
        tools=tools_list
    )
    
    return strands_agent
