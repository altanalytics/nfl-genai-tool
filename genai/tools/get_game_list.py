# get_game_list.py

import pandas as pd
import boto3
from io import StringIO
from typing import Any, Optional

# 1. Tool Specification
TOOL_SPEC = {
    "name": "get_game_list",
    "description": "Get NFL game list data from S3 and filter by season, week, team, or game ID.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "season": {
                    "type": "integer",
                    "description": "NFL season year (e.g., 2023, 2024)"
                },
                "week": {
                    "type": "integer",
                    "description": "NFL week number (1-18 for regular season, 19+ for playoffs)"
                },
                "team": {
                    "type": "string",
                    "description": "Team name, city, or abbreviation to search for (searches across home_team, away_team, home_team_city, away_team_city, home_team_abbrv, away_team_abbrv)"
                },
                "pbp_game_id": {
                    "type": "string",
                    "description": "Specific play-by-play game ID to filter by"
                }
            },
            "required": []
        }
    }
}

# 2. Tool Function
def get_game_list(tool, **kwargs: Any):
    """
    Reads NFL game data from S3 and filters based on provided parameters.
    
    Args:
        tool: Tool object containing toolUseId and input parameters
        **kwargs: Additional keyword arguments
        
    Returns:
        dict: Structured response with filtered game data
    """
    # CRITICAL: Log that this function is actually being called
    print("🚨 GET_GAME_LIST FUNCTION CALLED! 🚨")
    print(f"Tool input: {tool}")
    print(f"Kwargs: {kwargs}")
    
    # Extract tool parameters
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]

    # Get parameter values
    season = tool_input.get("season")
    week = tool_input.get("week")
    team = tool_input.get("team")
    pbp_game_id = tool_input.get("pbp_game_id")
    
    print(f"🔍 Searching for: season={season}, week={week}, team={team}, pbp_game_id={pbp_game_id}")

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
        
        # Apply filters
        filtered_df = df.copy()
        
        # Filter by season
        if season is not None:
            if 'season' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['season'] == season]
            else:
                return {
                    "toolUseId": tool_use_id,
                    "status": "error",
                    "content": [{"text": "Season column not found in the dataset"}]
                }
        
        # Filter by week
        if week is not None:
            if 'week' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['week'] == week]
            else:
                return {
                    "toolUseId": tool_use_id,
                    "status": "error",
                    "content": [{"text": "Week column not found in the dataset"}]
                }
        
        # Filter by team (OR search across multiple team columns)
        if team is not None:
            team_columns = ['home_team', 'away_team', 'home_team_city', 'away_team_city', 'home_team_abbrv', 'away_team_abbrv']
            available_team_columns = [col for col in team_columns if col in filtered_df.columns]
            
            if available_team_columns:
                # Reset index to avoid alignment issues when filtering
                filtered_df = filtered_df.reset_index(drop=True)
                # Create OR condition across all team columns (case-insensitive)
                team_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
                for col in available_team_columns:
                    team_mask |= filtered_df[col].str.contains(team, case=False, na=False)
                filtered_df = filtered_df[team_mask]
            else:
                return {
                    "toolUseId": tool_use_id,
                    "status": "error",
                    "content": [{"text": f"No team columns found in the dataset. Available columns: {list(filtered_df.columns)}"}]
                }
        
        # Filter by pbp_game_id
        if pbp_game_id is not None:
            if 'pbp_game_id' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['pbp_game_id'] == pbp_game_id]
            else:
                return {
                    "toolUseId": tool_use_id,
                    "status": "error",
                    "content": [{"text": "pbp_game_id column not found in the dataset"}]
                }
        
        # Prepare result
        num_games = len(filtered_df)
        
        if num_games == 0:
            result_text = "No games found matching the specified criteria."
        else:
            # Convert DataFrame to a readable format
            result_text = f"Found {num_games} game(s) matching the criteria:\n\n"
            
            # Display first 10 results to avoid overwhelming output
            display_df = filtered_df.head(10)
            result_text += display_df.to_string(index=False)
            
            if num_games > 10:
                result_text += f"\n\n... and {num_games - 10} more games. Use more specific filters to narrow results."
        
        # Return structured response
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": [{"text": result_text}]
        }
        
    except Exception as e:
        # Handle any errors
        error_message = f"Error retrieving game list: {str(e)}"
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": error_message}]
        }

# Attach TOOL_SPEC to function for Strands framework
get_game_list.TOOL_SPEC = TOOL_SPEC
