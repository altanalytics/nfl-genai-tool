# get_game_metadata.py

import pandas as pd
import boto3
from io import StringIO
from typing import Any

# 1. Tool Specification
TOOL_SPEC = {
    "name": "get_game_metadata",
    "description": "Get game metadata from game_list_clean.csv for a pbp_game_id. Returns the filtered row as JSON.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "pbp_game_id": {
                    "type": "string",
                    "description": "The pbp_game_id to get metadata for"
                }
            },
            "required": ["pbp_game_id"]
        }
    }
}

# 2. Tool Function
def get_game_metadata(tool, **kwargs: Any):
    """
    Retrieves game metadata from game_list_clean.csv as JSON.
    
    Args:
        tool: Tool object containing toolUseId and input parameters
        **kwargs: Additional keyword arguments
        
    Returns:
        dict: Structured response with game metadata as JSON
    """
    # Extract tool parameters
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]
    
    pbp_game_id = tool_input.get("pbp_game_id", "").strip()
    
    if not pbp_game_id:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "pbp_game_id is required"}]
        }
    
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Download game list CSV from S3
        bucket_name = 'alt-nfl-bucket'
        key = 'nfl_data/game_list_clean.csv'
        
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        
        # Read into pandas DataFrame
        df = pd.read_csv(StringIO(csv_content))
        
        # Filter for the specific game
        game_data = df[df['pbp_game_id'] == pbp_game_id]
        
        if len(game_data) == 0:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"No game found with pbp_game_id: {pbp_game_id}"}]
            }
        
        # Convert to JSON and return
        game_json = game_data.iloc[0].to_dict()
        
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "game_metadata": game_json,
            "content": [{"text": f"Game metadata for {pbp_game_id}: {game_json}"}]
        }
        
    except Exception as e:
        error_message = f"Error retrieving game metadata: {str(e)}"
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": error_message}]
        }

# Attach TOOL_SPEC to function for Strands framework
get_game_metadata.TOOL_SPEC = TOOL_SPEC
