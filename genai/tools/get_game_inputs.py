# get_game_inputs.py

import boto3
import json
from typing import Any

TOOL_SPEC = {
    "name": "get_game_inputs",
    "description": "Pull all input files for a specific game from S3 and return as JSON objects.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "unique_game_id": {
                    "type": "string",
                    "description": "Unique game identifier (e.g., '2024_2_18_DAL_WSH')"
                }
            },
            "required": ["unique_game_id"]
        }
    }
}

def get_game_inputs(tool, **kwargs: Any):
    """
    Pull all input files for a specific game from S3 and return as JSON objects.
    """
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]
    
    # Get parameters from tool input
    unique_game_id = tool_input.get("unique_game_id")
    
    try:
        # Initialize AWS session
        s3_client = boto3.client('s3')
        s3_bucket = "alt-nfl-bucket"
        
        # Parse the unique_game_id to construct S3 path
        # Format: YYYY_T_WW_TEAM1_TEAM2
        parts = unique_game_id.split('_')
        if len(parts) < 4:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Invalid unique_game_id format: {unique_game_id}"}]
            }
        
        season = parts[0]  # e.g., "2024"
        season_type_code = parts[1]  # e.g., "2"
        week = parts[2]  # e.g., "18"
        
        # Map season type code to folder name
        season_type_map = {
            "1": "preseason",
            "2": "regular-season", 
            "3": "post-season"
        }
        
        season_type_folder = season_type_map.get(season_type_code)
        if not season_type_folder:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Invalid season type code: {season_type_code}"}]
            }
        
        # Construct S3 prefix for input files using actual bucket structure
        # Format: nfl_espn_data/season_YYYY/season-type/week_XX/game_id/inputs/
        week_padded = week.zfill(2)  # Ensure 2-digit week (08 instead of 8)
        s3_prefix = f"nfl_espn_data/season_{season}/{season_type_folder}/week_{week_padded}/{unique_game_id}/inputs/"
        
        # List all files in the inputs directory
        response = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=s3_prefix)
        
        if 'Contents' not in response:
            return {
                "toolUseId": tool_use_id,
                "status": "success",
                "content": [{"text": f"No input files found for game {unique_game_id} at path: {s3_prefix}"}]
            }
        
        result_text = f"Input files for game {unique_game_id}:\n\n"
        
        # Process each file
        for obj in response['Contents']:
            file_key = obj['Key']
            file_name = file_key.split('/')[-1]  # Get just the filename
            
            if file_name:  # Skip directory entries
                try:
                    # Get file content
                    file_response = s3_client.get_object(Bucket=s3_bucket, Key=file_key)
                    file_content = file_response['Body'].read().decode('utf-8')
                    
                    result_text += f"=== {file_name} ===\n"
                    
                    # Try to parse as JSON for better formatting
                    try:
                        json_data = json.loads(file_content)
                        result_text += json.dumps(json_data, indent=2)
                    except json.JSONDecodeError:
                        # If not JSON, include as plain text
                        result_text += file_content
                    
                    result_text += "\n\n"
                    
                except Exception as file_error:
                    result_text += f"=== {file_name} ===\n"
                    result_text += f"Error reading file: {str(file_error)}\n\n"
        
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": [{"text": result_text}]
        }
        
    except Exception as e:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": f"Error retrieving game inputs: {str(e)}"}]
        }
