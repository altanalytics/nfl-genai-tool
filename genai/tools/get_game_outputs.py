# get_game_outputs.py

import boto3
import json
from typing import Dict, Any

def get_game_outputs(unique_game_id: str) -> str:
    """
    Pull all output files for a specific game from S3 and return as JSON objects.
    
    Args:
        unique_game_id: Unique game identifier (e.g., '2024_2_18_DAL_WSH')
        
    Returns:
        str: Formatted information about game output files and their contents
    """
    try:
        # Initialize AWS session
        s3_client = boto3.client('s3')
        s3_bucket = "alt-nfl-bucket"
        
        # Parse the unique_game_id to construct S3 path
        # Format: YYYY_T_WW_TEAM1_TEAM2
        parts = unique_game_id.split('_')
        if len(parts) < 4:
            return f"Invalid unique_game_id format: {unique_game_id}"
        
        season = parts[0]  # e.g., "2024"
        season_type_code = parts[1]  # e.g., "2"
        week = parts[2]  # e.g., "18"
        
        # Map season type code to folder name
        season_type_map = {
            "1": "preseason",
            "2": "regular-season", 
            "3": "post-season"
        }
        
        season_type = season_type_map.get(season_type_code)
        if not season_type:
            return f"Invalid season type code: {season_type_code}"
        
        # Format week with leading zero if needed
        week_formatted = f"week_{week.zfill(2)}"
        
        # Construct S3 path for outputs
        s3_path = f"nfl_espn_data/season_{season}/{season_type}/{week_formatted}/{unique_game_id}/outputs/"
        
        # List all objects in the folder
        response = s3_client.list_objects_v2(
            Bucket=s3_bucket,
            Prefix=s3_path
        )
        
        if 'Contents' not in response:
            return f"No files found in path: s3://{s3_bucket}/{s3_path}"
        
        # Dictionary to store all file contents
        game_outputs = {}
        
        # Process each file
        for obj in response['Contents']:
            file_key = obj['Key']
            filename = file_key.split('/')[-1]  # Get just the filename
            
            # Skip if it's just the folder itself
            if filename == '':
                continue
            
            try:
                # Get file content
                file_response = s3_client.get_object(Bucket=s3_bucket, Key=file_key)
                file_content = file_response['Body'].read().decode('utf-8')
                
                # Try to parse as JSON first
                try:
                    game_outputs[filename] = json.loads(file_content)
                except json.JSONDecodeError:
                    # If not JSON, store as string
                    game_outputs[filename] = file_content
                    
            except Exception as e:
                game_outputs[filename] = {"error": f"Failed to read file: {str(e)}"}
        
        # Prepare result text
        files_found = len([k for k in game_outputs.keys()])
        result_text = f"GAME OUTPUT FILES FOR: {unique_game_id}\n"
        result_text += f"S3 Path: s3://{s3_bucket}/{s3_path}\n"
        result_text += f"Files Found: {files_found}\n\n"
        
        if files_found == 0:
            result_text += "No output files found for this game."
        else:
            result_text += "FILES:\n"
            for filename, file_data in game_outputs.items():
                if isinstance(file_data, dict) and "error" not in file_data:
                    result_text += f"  {filename}: JSON object with {len(file_data)} keys\n"
                elif isinstance(file_data, str):
                    result_text += f"  {filename}: Text file ({len(file_data)} characters)\n"
                else:
                    result_text += f"  {filename}: {type(file_data)}\n"
            
            # Show sample of first file if available
            first_file = list(game_outputs.keys())[0]
            result_text += f"\nSAMPLE FROM {first_file}:\n"
            sample_data = game_outputs[first_file]
            if isinstance(sample_data, dict):
                # Show first few keys if it's a dict
                sample_keys = list(sample_data.keys())[:5]
                for key in sample_keys:
                    result_text += f"  {key}: {type(sample_data[key])}\n"
                if len(sample_data) > 5:
                    result_text += f"  ... and {len(sample_data) - 5} more keys\n"
            elif isinstance(sample_data, str):
                # Show first 200 characters if it's a string
                result_text += f"  {sample_data[:200]}...\n"
        
        return result_text
        
    except Exception as e:
        return f"Error retrieving game outputs: {str(e)}"
