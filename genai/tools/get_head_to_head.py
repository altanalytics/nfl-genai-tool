# get_head_to_head.py

import pandas as pd
import boto3
from io import StringIO
from typing import Any, Optional

# 1. Tool Specification
TOOL_SPEC = {
    "name": "get_head_to_head",
    "description": "Find head-to-head matchups between two specific NFL teams, regardless of home/away status.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "team1": {
                    "type": "string",
                    "description": "First team name, city, or abbreviation"
                },
                "team2": {
                    "type": "string",
                    "description": "Second team name, city, or abbreviation"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of games to return (default: 10)",
                    "default": 10
                }
            },
            "required": ["team1", "team2"]
        }
    }
}

# 2. Tool Function
def get_head_to_head(tool, **kwargs: Any):
    """
    Finds head-to-head matchups between two specific teams.
    
    Args:
        tool: Tool object containing toolUseId and input parameters
        **kwargs: Additional keyword arguments
        
    Returns:
        dict: Structured response with head-to-head game data
    """
    # Extract tool parameters
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]

    # Get parameter values
    team1 = tool_input.get("team1")
    team2 = tool_input.get("team2")
    limit = tool_input.get("limit", 10)

    if not team1 or not team2:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "Both team1 and team2 parameters are required"}]
        }

    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Download CSV from S3
        bucket_name = 'alt-nfl-bucket'
        key = 'nfl_data/game_list_clean.csv'
        
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        
        # Read into pandas DataFrame
        df = pd.read_csv(StringIO(csv_content))
        
        # Define team columns to search
        team_columns = ['home_team', 'away_team', 'home_team_city', 'away_team_city', 'home_team_abbrv', 'away_team_abbrv']
        available_team_columns = [col for col in team_columns if col in df.columns]
        
        if not available_team_columns:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"No team columns found in the dataset. Available columns: {list(df.columns)}"}]
            }
        
        # Create masks for each team (case-insensitive)
        team1_mask = pd.Series([False] * len(df), index=df.index)
        team2_mask = pd.Series([False] * len(df), index=df.index)
        
        for col in available_team_columns:
            team1_mask |= df[col].str.contains(team1, case=False, na=False)
            team2_mask |= df[col].str.contains(team2, case=False, na=False)
        
        # Find games where BOTH teams are present (head-to-head matchups)
        head_to_head_mask = team1_mask & team2_mask
        head_to_head_games = df[head_to_head_mask]
        
        # Sort by date (most recent first) and limit results
        if 'game_date' in head_to_head_games.columns:
            head_to_head_games = head_to_head_games.sort_values('game_date', ascending=False)
        elif 'date' in head_to_head_games.columns:
            head_to_head_games = head_to_head_games.sort_values('date', ascending=False)
        
        head_to_head_games = head_to_head_games.head(limit)
        
        # Prepare result
        num_games = len(head_to_head_games)
        
        if num_games == 0:
            result_text = f"No head-to-head matchups found between {team1} and {team2}."
        else:
            result_text = f"Found {num_games} head-to-head matchup(s) between {team1} and {team2}:\n\n"
            result_text += head_to_head_games.to_string(index=False)
        
        # Return structured response
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": [{"text": result_text}]
        }
        
    except Exception as e:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": f"Error retrieving head-to-head games: {str(e)}"}]
        }

# 3. Export the tool
__all__ = ["get_head_to_head", "TOOL_SPEC"]
