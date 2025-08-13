# get_game_outputs.py

from typing import Any
from tools.game_utils import read_game_files

# 1. Tool Specification
TOOL_SPEC = {
    "name": "get_game_outputs",
    "description": "Retrieve and read all output files for a specific NFL game from S3 based on pbp_game_id.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "pbp_game_id": {
                    "type": "string",
                    "description": "The play-by-play game ID to retrieve output files for"
                }
            },
            "required": ["pbp_game_id"]
        }
    }
}

# 2. Tool Function
def get_game_outputs(tool, **kwargs: Any):
    """
    Retrieves all output files for a specific game from S3.
    
    Args:
        tool: Tool object containing toolUseId and input parameters
        **kwargs: Additional keyword arguments
        
    Returns:
        dict: Structured response with all output files content
    """
    # Extract tool parameters
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]
    
    # Get parameter values
    pbp_game_id = tool_input.get("pbp_game_id")
    
    if not pbp_game_id:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "pbp_game_id is required"}]
        }
    
    # Use shared utility to read game files
    result = read_game_files(pbp_game_id, "outputs")
    
    if not result["success"]:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": result["error"]}]
        }
    
    # Prepare result summary
    file_count = result["file_count"]
    game_info = result["game_info"]
    files_data = result["files"]
    
    if file_count == 0:
        result_text = f"No readable output files found for game {pbp_game_id}"
    else:
        result_text = f"Successfully retrieved {file_count} output files for game {pbp_game_id} (Season {game_info['season']}, Week {game_info['week']}):\n\n"
        
        # Add summary of files
        for filename, file_info in files_data.items():
            if 'error' in file_info:
                result_text += f"❌ {filename}: {file_info['error']}\n"
            else:
                size_kb = file_info['size_bytes'] / 1024
                result_text += f"✅ {filename}: {size_kb:.1f} KB\n"
        
        result_text += f"\nS3 Path: {game_info['s3_path']}\n"
        result_text += "\nOutput file contents are available in the response data."
    
    # Return structured response with file contents
    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": result_text}],
        "data": {
            "game_info": game_info,
            "output_files": files_data,
            "file_count": file_count
        }
    }
