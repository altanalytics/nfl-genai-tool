# find_games_by_teams.py

import pandas as pd
import boto3
from io import StringIO
from typing import Any, Optional, List

# 1. Tool Specification
TOOL_SPEC = {
    "name": "find_games_by_teams",
    "description": "Find NFL games by team_id(s) and season. Returns user-friendly schedule for selection, then converts selection to pbp_game_id.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "team_id_1": {
                    "type": "string",
                    "description": "First team ID (e.g., 'NE', 'KC', 'DAL') - required"
                },
                "team_id_2": {
                    "type": "string",
                    "description": "Second team ID (optional) - if provided, will find games between these two specific teams"
                },
                "season": {
                    "type": "integer",
                    "description": "NFL season year (e.g., 2023, 2024) - required"
                },
                "week": {
                    "type": "integer",
                    "description": "Optional: specific week number to filter by (1-18 for regular season, 19+ for playoffs)"
                },
                "user_selection": {
                    "type": "string",
                    "description": "Optional: User's selection from the schedule (e.g., 'Week 5 vs Chiefs', 'Game 3') to get the pbp_game_id"
                }
            },
            "required": ["team_id_1", "season"]
        }
    }
}

# 2. Tool Function
def find_games_by_teams(tool, **kwargs: Any):
    """
    Finds NFL games by team_id(s) and season. Shows user-friendly schedule or converts selection to pbp_game_id.
    
    Args:
        tool: Tool object containing toolUseId and input parameters
        **kwargs: Additional keyword arguments
        
    Returns:
        dict: Structured response with schedule or pbp_game_id
    """
    # Extract tool parameters
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]
    
    team_id_1 = tool_input.get("team_id_1", "").strip().upper()
    team_id_2 = tool_input.get("team_id_2", "").strip().upper() if tool_input.get("team_id_2") else None
    season = tool_input.get("season")
    week = tool_input.get("week")
    user_selection = tool_input.get("user_selection", "").strip()
    
    # Validation
    if not team_id_1:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "team_id_1 is required"}]
        }
    
    if not season:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "season is required"}]
        }
    
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Download game list CSV from S3
        bucket_name = 'alt-nfl-bucket'
        key = 'admin/game_list_clean.csv'
        
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        
        # Read into pandas DataFrame
        df = pd.read_csv(StringIO(csv_content))
        
        # Check if required columns exist
        required_columns = ['season', 'updated_short_name', 'pbp_game_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Missing required columns: {missing_columns}. Available columns: {list(df.columns)}"}]
            }
        
        # Filter by season first
        filtered_df = df[df['season'] == season].copy()
        
        if len(filtered_df) == 0:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"No games found for season {season}. Available seasons: {sorted(df['season'].unique())}"}]
            }
        
        # Filter by week if provided
        if week is not None:
            if 'week' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['week'] == week]
                if len(filtered_df) == 0:
                    return {
                        "toolUseId": tool_use_id,
                        "status": "error",
                        "content": [{"text": f"No games found for season {season}, week {week}"}]
                    }
        
        # Filter by team(s) using updated_short_name (CASE INSENSITIVE)
        if team_id_2:
            # Looking for games between two specific teams
            team_mask = (
                (filtered_df['updated_short_name'].str.contains(f'{team_id_1}', case=False, na=False)) &
                (filtered_df['updated_short_name'].str.contains(f'{team_id_2}', case=False, na=False))
            )
            search_description = f"games between {team_id_1} and {team_id_2}"
        else:
            # Looking for any games involving team_id_1
            team_mask = filtered_df['updated_short_name'].str.contains(
                f'{team_id_1}', 
                case=False, 
                na=False
            )
            search_description = f"games involving {team_id_1}"
        
        games_found = filtered_df[team_mask].copy()
        
        # Sort by week if available, otherwise by date-related columns
        if 'week' in games_found.columns:
            games_found = games_found.sort_values('week')
        elif 'game_date' in games_found.columns:
            games_found = games_found.sort_values('game_date')
        
        num_games = len(games_found)
        
        if num_games == 0:
            # Use AI knowledge to suggest alternatives
            result_text = f"❌ No {search_description} found for {season} season"
            if week:
                result_text += f", week {week}"
            
            # Provide helpful suggestions
            result_text += f"\n\n🤔 Let me help you find the right game:"
            result_text += f"\n• Double-check the team name and season"
            result_text += f"\n• Try searching for just one team first"
            result_text += f"\n• The team might have played under a different name that season"
            
            if not team_id_2:
                result_text += f"\n\n💡 Would you like me to show all {team_id_1} games for {season}?"
            
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": result_text}]
            }
        
        # If user made a selection, find the pbp_game_id
        if user_selection:
            # Try to match user selection to a game
            selection_lower = user_selection.lower()
            matched_game = None
            
            # Try different matching strategies
            for idx, row in games_found.iterrows():
                game_desc = row['updated_short_name'].lower()
                week_str = f"week {row.get('week', 'N/A')}".lower()
                
                # Check if selection matches game description or week
                if (selection_lower in game_desc or 
                    game_desc in selection_lower or
                    selection_lower in week_str or
                    str(row.get('week', '')) in user_selection):
                    matched_game = row
                    break
            
            if matched_game is not None:
                pbp_game_id = matched_game['pbp_game_id']
                game_desc = matched_game['updated_short_name']
                week_info = f"Week {matched_game.get('week', 'N/A')}" if 'week' in matched_game else ""
                
                result_text = f"✅ Game Selected!\n"
                result_text += f"📋 {game_desc}\n"
                if week_info:
                    result_text += f"📅 {week_info}\n"
                result_text += f"🆔 Game ID: {pbp_game_id}\n\n"
                result_text += f"Is this the correct game for your recap?"
                
                return {
                    "toolUseId": tool_use_id,
                    "status": "success",
                    "pbp_game_id": pbp_game_id,
                    "game_description": game_desc,
                    "content": [{"text": result_text}]
                }
            else:
                result_text = f"❌ Could not match your selection '{user_selection}' to any game.\n\n"
                result_text += f"Please select from the available options below."
        
        # Show user-friendly schedule (no pbp_game_id visible)
        result_text = f"✅ Found {num_games} {search_description} in {season}"
        if week:
            result_text += f", week {week}"
        result_text += ":\n\n"
        
        # Create user-friendly display
        for idx, (_, row) in enumerate(games_found.iterrows(), 1):
            game_desc = row['updated_short_name']
            week_info = f"Week {row.get('week', 'N/A')}" if 'week' in row else ""
            date_info = f" ({row.get('game_date', 'N/A')})" if 'game_date' in row else ""
            
            result_text += f"{idx}. {game_desc}"
            if week_info:
                result_text += f" - {week_info}"
            if date_info and date_info != " (N/A)":
                result_text += date_info
            result_text += "\n"
        
        result_text += f"\n🎯 Please tell me which game you'd like a recap for (e.g., 'Game 1', 'Week 5', or describe the matchup)."
        
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "games_data": games_found.to_dict('records'),  # Store for selection matching
            "num_games_found": num_games,
            "content": [{"text": result_text}]
        }
        
    except Exception as e:
        error_message = f"Error finding games: {str(e)}"
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": error_message}]
        }

# Attach TOOL_SPEC to function for Strands framework
find_games_by_teams.TOOL_SPEC = TOOL_SPEC
