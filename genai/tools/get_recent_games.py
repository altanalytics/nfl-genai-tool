# get_recent_games.py

import pandas as pd
import boto3
from io import StringIO
from typing import Any, Optional
from datetime import datetime

# 1. Tool Specification
TOOL_SPEC = {
    "name": "get_recent_games",
    "description": "Find the 3 most recent games BEFORE a selected game for each team involved in that game.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "pbp_game_id": {
                    "type": "string",
                    "description": "The game ID of the selected game to find recent games before"
                },
                "games_per_team": {
                    "type": "integer",
                    "description": "Number of recent games to find per team (default: 3)",
                    "default": 3
                }
            },
            "required": ["pbp_game_id"]
        }
    }
}

# 2. Tool Function
def get_recent_games(tool, **kwargs: Any):
    """
    Finds the most recent games before a selected game for each team.
    
    Args:
        tool: Tool object containing toolUseId and input parameters
        **kwargs: Additional keyword arguments
        
    Returns:
        dict: Structured response with recent games for each team
    """
    # Extract tool parameters
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]

    # Get parameter values
    pbp_game_id = tool_input.get("pbp_game_id")
    games_per_team = tool_input.get("games_per_team", 3)

    if not pbp_game_id:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "pbp_game_id parameter is required"}]
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
        
        # Find the selected game
        selected_game = df[df['pbp_game_id'] == pbp_game_id]
        
        if selected_game.empty:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Selected game with ID {pbp_game_id} not found"}]
            }
        
        # Get the selected game details
        selected_row = selected_game.iloc[0]
        home_team = selected_row.get('home_team', '')
        away_team = selected_row.get('away_team', '')
        selected_date = selected_row.get('game_date', selected_row.get('date', ''))
        
        if not home_team or not away_team:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": "Could not identify home and away teams from selected game"}]
            }
        
        # Convert selected date to datetime for comparison
        try:
            if isinstance(selected_date, str):
                selected_datetime = pd.to_datetime(selected_date)
            else:
                selected_datetime = selected_date
        except:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": "Could not parse game date from selected game"}]
            }
        
        # Convert game_date column to datetime
        date_col = 'game_date' if 'game_date' in df.columns else 'date'
        df[date_col] = pd.to_datetime(df[date_col])
        
        # Find recent games for home team
        home_team_games = df[
            ((df['home_team'] == home_team) | (df['away_team'] == home_team)) &
            (df[date_col] < selected_datetime)
        ].sort_values(date_col, ascending=False).head(games_per_team)
        
        # Find recent games for away team
        away_team_games = df[
            ((df['home_team'] == away_team) | (df['away_team'] == away_team)) &
            (df[date_col] < selected_datetime)
        ].sort_values(date_col, ascending=False).head(games_per_team)
        
        # Prepare result
        result_text = f"Recent games before {pbp_game_id} ({home_team} vs {away_team}):\n\n"
        
        result_text += f"**{home_team} - Last {games_per_team} games:**\n"
        if home_team_games.empty:
            result_text += "No recent games found\n"
        else:
            result_text += home_team_games.to_string(index=False)
        
        result_text += f"\n\n**{away_team} - Last {games_per_team} games:**\n"
        if away_team_games.empty:
            result_text += "No recent games found\n"
        else:
            result_text += away_team_games.to_string(index=False)
        
        result_text += f"\n\n**Total games found:** {len(home_team_games)} for {home_team}, {len(away_team_games)} for {away_team}"
        
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
            "content": [{"text": f"Error retrieving recent games: {str(e)}"}]
        }

# 3. Export the tool
__all__ = ["get_recent_games", "TOOL_SPEC"]
