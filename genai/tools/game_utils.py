# game_utils.py

import boto3
import pandas as pd
from io import StringIO
from typing import Dict, Tuple, Any

def get_game_info_from_id(pbp_game_id: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Retrieve game information from the game list CSV based on pbp_game_id.
    
    Args:
        pbp_game_id: The play-by-play game ID
        
    Returns:
        Tuple of (success: bool, result: dict)
        If success=True, result contains game info
        If success=False, result contains error message
    """
    try:
        s3_client = boto3.client('s3')
        bucket_name = 'alt-nfl-bucket'
        game_list_key = 'nfl_data/game_list_clean.csv'
        
        # Get game list from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=game_list_key)
        csv_content = response['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_content))
        
        # Find the game
        game_row = df[df['pbp_game_id'] == pbp_game_id]
        
        if game_row.empty:
            return False, {"error": f"Game with pbp_game_id '{pbp_game_id}' not found in game list"}
        
        game_info = game_row.iloc[0]
        return True, {
            "season": int(game_info['season']),
            "week": int(game_info['week']),
            "pbp_game_id": pbp_game_id
        }
        
    except Exception as e:
        return False, {"error": f"Error reading game list: {str(e)}"}


def read_game_files(pbp_game_id: str, folder_type: str) -> Dict[str, Any]:
    """
    Read all files from a specific game folder (inputs or outputs).
    
    Args:
        pbp_game_id: The play-by-play game ID
        folder_type: Either 'inputs' or 'outputs'
        
    Returns:
        Dictionary with file contents and metadata
    """
    # Get game info
    success, game_data = get_game_info_from_id(pbp_game_id)
    
    if not success:
        return {
            "success": False,
            "error": game_data["error"]
        }
    
    season = game_data["season"]
    week = game_data["week"]
    
    try:
        s3_client = boto3.client('s3')
        bucket_name = 'alt-nfl-bucket'
        
        # Construct the S3 path
        folder_path = f"nfl_data/{season}/week_{week:02d}/{pbp_game_id}/{folder_type}/"
        
        # List all files in the folder
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=folder_path
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing files in {folder_path}: {str(e)}"
            }
        
        if 'Contents' not in response:
            return {
                "success": False,
                "error": f"No files found in {folder_path}"
            }
        
        # Read all files
        files_data = {}
        file_count = 0
        
        for obj in response['Contents']:
            file_key = obj['Key']
            
            # Skip if it's just the folder itself
            if file_key.endswith('/'):
                continue
                
            # Extract just the filename from the full path
            filename = file_key.split('/')[-1]
            
            try:
                # Read the file content
                file_response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
                file_content = file_response['Body'].read().decode('utf-8')
                
                files_data[filename] = {
                    'content': file_content,
                    'size_bytes': len(file_content.encode('utf-8')),
                    's3_path': f"s3://{bucket_name}/{file_key}"
                }
                file_count += 1
                
            except Exception as e:
                files_data[filename] = {
                    'error': f"Failed to read file: {str(e)}",
                    's3_path': f"s3://{bucket_name}/{file_key}"
                }
        
        return {
            "success": True,
            "game_info": {
                "pbp_game_id": pbp_game_id,
                "season": season,
                "week": week,
                "s3_path": f"s3://{bucket_name}/{folder_path}"
            },
            "files": files_data,
            "file_count": file_count,
            "folder_type": folder_type
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving game {folder_type}: {str(e)}"
        }
