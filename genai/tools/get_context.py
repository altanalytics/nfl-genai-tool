# get_context.py

import pandas as pd
import boto3
from io import StringIO
from typing import Any

TOOL_SPEC = {
    "name": "get_context",
    "description": "Get context for a specific game by returning previous games for each team and their head-to-head history.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "unique_game_id": {
                    "type": "string",
                    "description": "Unique game identifier (e.g., '2024_2_18_DAL_WSH')"
                },
                "context": {
                    "type": "integer",
                    "description": "Number of previous games to return for each category"
                },
                "include_preseason": {
                    "type": "boolean",
                    "description": "Whether to include preseason games (default: false)"
                }
            },
            "required": ["unique_game_id", "context"]
        }
    }
}

def get_context(tool, **kwargs: Any):
    """
    Get context for a specific game by returning previous games for each team and their head-to-head history.
    """
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]
    
    # Get parameters from tool input
    unique_game_id = tool_input.get("unique_game_id")
    context = tool_input.get("context")
    include_preseason = tool_input.get("include_preseason", False)
    
    try:
        # Initialize AWS session
        s3_client = boto3.client('s3')
        s3_bucket = "alt-nfl-bucket"
        
        # Load schedule data from S3
        response = s3_client.get_object(Bucket=s3_bucket, Key="admin/clean_schedule.csv")
        schedule_df = pd.read_csv(StringIO(response['Body'].read().decode('utf-8')))
        schedule_df['date_time'] = pd.to_datetime(schedule_df['date_time'])
        schedule_df = schedule_df.sort_values('date_time', ascending=True)
        
        # Find the target game
        target_game = schedule_df[schedule_df['unique_id'] == unique_game_id]
        if target_game.empty:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Game with ID '{unique_game_id}' not found"}]
            }
        
        target_game = target_game.iloc[0]
        home_team = target_game['home_team']
        away_team = target_game['away_team']
        target_date = target_game['date_time']
        
        # Filter out preseason if requested
        if not include_preseason:
            schedule_df = schedule_df[schedule_df['season_type'] != 1]
        
        # Get games before the target date
        before_target = schedule_df[schedule_df['date_time'] < target_date]
        
        # Get previous games for home team
        home_team_games = before_target[
            (before_target['home_team'] == home_team) | 
            (before_target['away_team'] == home_team)
        ].tail(context)
        
        # Get previous games for away team
        away_team_games = before_target[
            (before_target['home_team'] == away_team) | 
            (before_target['away_team'] == away_team)
        ].tail(context)
        
        # Get head-to-head history
        h2h_games = before_target[
            ((before_target['home_team'] == home_team) & (before_target['away_team'] == away_team)) |
            ((before_target['home_team'] == away_team) & (before_target['away_team'] == home_team))
        ].tail(context)
        
        # Prepare result
        result_text = f"Context for game {unique_game_id} ({away_team} @ {home_team}):\n\n"
        
        # Home team context
        result_text += f"=== {home_team} Previous {context} Games ===\n"
        if not home_team_games.empty:
            columns = ['unique_id', 'matchup', 'date', 'home_score', 'away_score']
            result_text += home_team_games[columns].to_string(index=False)
        else:
            result_text += "No previous games found"
        result_text += "\n\n"
        
        # Away team context
        result_text += f"=== {away_team} Previous {context} Games ===\n"
        if not away_team_games.empty:
            columns = ['unique_id', 'matchup', 'date', 'home_score', 'away_score']
            result_text += away_team_games[columns].to_string(index=False)
        else:
            result_text += "No previous games found"
        result_text += "\n\n"
        
        # Head-to-head context
        result_text += f"=== {home_team} vs {away_team} Head-to-Head (Last {context}) ===\n"
        if not h2h_games.empty:
            columns = ['unique_id', 'matchup', 'date', 'home_score', 'away_score']
            result_text += h2h_games[columns].to_string(index=False)
        else:
            result_text += "No previous head-to-head games found"
        
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": [{"text": result_text}]
        }
        
    except Exception as e:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": f"Error retrieving context: {str(e)}"}]
        }
