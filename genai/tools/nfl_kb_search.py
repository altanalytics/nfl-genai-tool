# nfl_kb_search.py

from strands_tools.retrieve import retrieve
from typing import Any

# 1. Tool Specification
TOOL_SPEC = {
    "name": "nfl_kb_search",
    "description": """Search the NFL knowledge base for statistical information, historical data, and analysis.

This tool provides access to comprehensive NFL data, enabling queries about:
- Player statistics and performance metrics
- Team records and historical data
- Game results and play-by-play analysis
- Season trends and comparative analysis
- Draft information and player profiles

Results are sorted by relevance score and include source metadata.""",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The query to search for in the NFL knowledge base"
                },
                "numberOfResults": {
                    "type": "integer",
                    "description": "The maximum number of results to return. Default is 5.",
                    "default": 5
                },
                "score": {
                    "type": "number",
                    "description": "Minimum relevance score threshold (0.0-1.0). Results below this score will be filtered out. Default is 0.4.",
                    "default": 0.4,
                    "minimum": 0.0,
                    "maximum": 1.0
                }
            },
            "required": ["text"]
        }
    }
}

# 2. Tool Function
def nfl_kb_search(tool, **kwargs: Any):
    """
    Search the NFL knowledge base with pre-configured settings.
    
    This is a wrapper around the retrieve tool that automatically uses
    the correct knowledge base ID and region for NFL data.
    
    Args:
        tool: Tool object containing toolUseId and input parameters
        **kwargs: Additional keyword arguments
        
    Returns:
        dict: Structured response from the knowledge base search
    """
    # Extract the original input
    tool_input = tool["input"]
    
    # Add the pre-configured knowledge base settings
    enhanced_input = {
        **tool_input,
        "knowledgeBaseId": "RRKMVWLTTG",
        "region": "us-east-1"
    }
    
    # Create a new tool object with the enhanced input
    enhanced_tool = {
        **tool,
        "input": enhanced_input
    }
    
    # Call the original retrieve function with our pre-configured settings
    return retrieve(enhanced_tool, **kwargs)

# Attach TOOL_SPEC to function for Strands framework
nfl_kb_search.TOOL_SPEC = TOOL_SPEC
