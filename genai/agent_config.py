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
        personality: Either 'nfl_with_kb', 'nfl_without_kb', or custom prompt
        model: The model ID being used
        
    Returns:
        str: Complete system prompt with rules appended
    """
    # Load rules that apply to all prompts
    rules = load_prompt_from_file('rules')
    
    # Handle specific personalities
    if personality in ['nfl_game_recap', 'nfl_analyst']:
        if personality == 'nfl_analyst':
            base_prompt = load_prompt_from_file('nfl_analyst')
        else:
            base_prompt = load_prompt_from_file('nfl_tools')
    else:
        # Treat as custom system prompt
        base_prompt = personality
    
    # Replace model placeholder with actual model name
    base_prompt = base_prompt.replace('[current model name]', model)
    
    # Combine base prompt with rules
    return f"{base_prompt}\n\n{rules}"

def create_strands_agent(model = 'us.anthropic.claude-sonnet-4-20250514-v1:0',
                         personality = 'nfl_game_recap',
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
        personality (str): Either 'nfl_game_recap', 'nfl_analyst', or custom system prompt
        session_id (str): Session ID for S3 session management
        s3_bucket (str): S3 bucket for session storage
        s3_prefix (str): S3 prefix for session storage
        tools (list): Optional list of tools to use (for MCP integration)
        
    Returns:
        Agent: Configured agent ready for use
    """
    
    # Model-specific max token limits
    model_token_limits = {
        'us.anthropic.claude-3-5-haiku-20241022-v1:0': 8000,  # Haiku limit is 8192, use 8000 for safety
        'anthropic.claude-3-5-haiku-20241022-v1:0': 8000,     # Non-cross-region version
    }
    
    # Get max tokens for the specific model, default to 20000 for other models
    max_tokens = model_token_limits.get(model, 10000)
    
    # Check if this is an Anthropic model that will use thinking
    is_anthropic_model = model.startswith('us.anthropic.') or model.startswith('anthropic.')
    
    # Configure the Bedrock model with Anthropic thinking capabilities
    bedrock_model_config = {
        "model_id": model,
        "max_tokens": max_tokens,
        #"top_p": 0.8,
    }
    
    # Add thinking configuration for Anthropic models
    if is_anthropic_model:
        bedrock_model_config["additional_request_fields"] = {
            "anthropic_beta": ["interleaved-thinking-2025-05-14"],
            "thinking": {
                "type": "enabled",
                "budget_tokens": 2048
            }
        }
        # Anthropic requires temperature=1 when thinking is enabled
        bedrock_model_config["temperature"] = 1
    else:
        # Use custom temperature for non-Anthropic models
        bedrock_model_config["temperature"] = 0.3
    
    bedrock_model = BedrockModel(**bedrock_model_config)

    # Configure conversation management for production
    conversation_manager = SlidingWindowConversationManager(
        window_size=10,  # Limit history size
    )

    # Get the system prompt based on personality
    system_prompt = get_system_prompt(personality, model)
    
    print(f"Received personality parameter: '{personality}'")
    print(f"Using system prompt: {system_prompt}")

    # Configure tools based on personality
    # Core tools (always available for NFL personalities)
    base_tools = [get_schedules, get_context, get_game_inputs, get_game_outputs]
    
    # Configure tools based on personality
    if tools is not None:
        # Use provided tools (e.g., from MCP client for nfl_analyst)
        print(f"Using provided MCP tools: {[getattr(tool, 'tool_name', str(tool)) for tool in tools]}")
        tools_list = tools
    elif personality == 'nfl_game_recap':
        tools_list = base_tools  # Only the 4 core tools: schedules, context, game_inputs, game_outputs
        print("NFL Game Recap Specialist - 4 core tools available")
    elif personality == 'nfl_analyst':
        # This should use MCP tools, but fallback to empty if no tools provided
        tools_list = []
        print("NFL Analyst - expecting MCP tools to be provided")
    else:
        tools_list = base_tools
        print("Using base NFL tools for custom personality")

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

    # Debug: Print tool information
    print(f"DEBUG: Number of tools configured: {len(tools_list)}")
    for i, tool in enumerate(tools_list):
        print(f"DEBUG: Tool {i}: {tool.__name__ if hasattr(tool, '__name__') else str(tool)}")
    
    # Create and return the agent
    strands_agent = Agent(
        model=bedrock_model,
        system_prompt=system_prompt,
        conversation_manager=conversation_manager,
        session_manager=session_manager,  # Add session manager
        # Adding tools is what triggers "Thinking..." in the UI
        tools=tools_list
    )
    
    print(f"DEBUG: Agent created successfully with {len(tools_list)} tools")
    return strands_agent
