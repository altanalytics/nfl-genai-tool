# get_context_games.py

import pandas as pd
import boto3
from io import StringIO
from typing import Any, List, Dict

# 1. Tool Specification
TOOL_SPEC = {
    "name": "get_context_games",
    "description": "Get 9 context games for a target game: 3 recent games for each team + 3 recent head-to-head games (all before the target game).",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "pbp_game_id": {
                    "type": "string",
                    "description": "The target game's pbp_game_id to get context for"
                }
            },
            "required": ["pbp_game_id"]
        }
    }
}

# 2. Tool Function
def get_context_games(tool, **kwargs: Any):
    """
    Gets 9 context games for analysis:
    - Group 1: Last 3 games for Team A (before target game)
    - Group 2: Last 3 games for Team B (before target game)  
    - Group 3: Last 3 head-to-head games (before target game)
    
    Args:
        tool: Tool object containing toolUseId and input parameters
        **kwargs: Additional keyword arguments
        
    Returns:
        dict: Structured response with 9 context games organized in groups
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
        
        # Find the target game
        target_game = df[df['pbp_game_id'] == pbp_game_id]
        
        if len(target_game) == 0:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Target game with pbp_game_id '{pbp_game_id}' not found"}]
            }
        
        target_game = target_game.iloc[0]
        
        # Get team abbreviations from target game
        team_a = target_game.get('home_team_abbrv', '').strip().upper()
        team_b = target_game.get('away_team_abbrv', '').strip().upper()
        
        if not team_a or not team_b:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Could not extract team abbreviations from target game. Available columns: {list(df.columns)}"}]
            }
        
        # Convert target game identifier to comparable format for filtering
        # We need a way to filter games that occurred BEFORE this game
        target_season = target_game.get('season')
        target_week = target_game.get('week')
        
        if pd.isna(target_season) or pd.isna(target_week):
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Target game missing season or week information"}]
            }
        
        # Create a filter for games BEFORE the target game
        # Games are "before" if: (season < target_season) OR (season == target_season AND week < target_week)
        before_target_mask = (
            (df['season'] < target_season) | 
            ((df['season'] == target_season) & (df['week'] < target_week))
        )
        
        games_before_target = df[before_target_mask].copy()
        
        if len(games_before_target) == 0:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"No games found before the target game (Season {target_season}, Week {target_week})"}]
            }
        
        # Sort by season and week (most recent first)
        games_before_target = games_before_target.sort_values(['season', 'week'], ascending=[False, False])
        
        # GROUP 1: Last 3 games for Team A
        team_a_mask = games_before_target['updated_short_name'].str.contains(team_a, case=False, na=False)
        team_a_games = games_before_target[team_a_mask].head(3)
        
        # GROUP 2: Last 3 games for Team B  
        team_b_mask = games_before_target['updated_short_name'].str.contains(team_b, case=False, na=False)
        team_b_games = games_before_target[team_b_mask].head(3)
        
        # GROUP 3: Last 3 head-to-head games
        h2h_mask = (
            games_before_target['updated_short_name'].str.contains(team_a, case=False, na=False) &
            games_before_target['updated_short_name'].str.contains(team_b, case=False, na=False)
        )
        h2h_games = games_before_target[h2h_mask].head(3)
        
        # Prepare results
        result_text = f"✅ Found context games for {target_game['updated_short_name']} (Season {target_season}, Week {target_week}):\n\n"
        
        # Group 1 Results
        result_text += f"📊 GROUP 1 - Recent {team_a} games ({len(team_a_games)} found):\n"
        if len(team_a_games) > 0:
            for idx, (_, game) in enumerate(team_a_games.iterrows(), 1):
                result_text += f"  {idx}. {game['updated_short_name']} (S{game['season']} W{game['week']}) - {game['pbp_game_id']}\n"
        else:
            result_text += f"  No recent {team_a} games found before target game\n"
        
        result_text += f"\n📊 GROUP 2 - Recent {team_b} games ({len(team_b_games)} found):\n"
        if len(team_b_games) > 0:
            for idx, (_, game) in enumerate(team_b_games.iterrows(), 1):
                result_text += f"  {idx}. {game['updated_short_name']} (S{game['season']} W{game['week']}) - {game['pbp_game_id']}\n"
        else:
            result_text += f"  No recent {team_b} games found before target game\n"
        
        result_text += f"\n📊 GROUP 3 - Recent {team_a} vs {team_b} games ({len(h2h_games)} found):\n"
        if len(h2h_games) > 0:
            for idx, (_, game) in enumerate(h2h_games.iterrows(), 1):
                result_text += f"  {idx}. {game['updated_short_name']} (S{game['season']} W{game['week']}) - {game['pbp_game_id']}\n"
        else:
            result_text += f"  No recent {team_a} vs {team_b} games found before target game\n"
        
        total_context_games = len(team_a_games) + len(team_b_games) + len(h2h_games)
        result_text += f"\n🎯 Total context games found: {total_context_games}/9"
        
        # Return structured data
        context_games = {
            "target_game": {
                "pbp_game_id": pbp_game_id,
                "description": target_game['updated_short_name'],
                "season": int(target_season),
                "week": int(target_week),
                "team_a": team_a,
                "team_b": team_b
            },
            "group_1_team_a": team_a_games[['pbp_game_id', 'updated_short_name', 'season', 'week']].to_dict('records'),
            "group_2_team_b": team_b_games[['pbp_game_id', 'updated_short_name', 'season', 'week']].to_dict('records'),
            "group_3_head_to_head": h2h_games[['pbp_game_id', 'updated_short_name', 'season', 'week']].to_dict('records')
        }
        
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "context_games": context_games,
            "total_games_found": total_context_games,
            "content": [{"text": result_text}]
        }
        
    except Exception as e:
        error_message = f"Error getting context games: {str(e)}"
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": error_message}]
        }

# Attach TOOL_SPEC to function for Strands framework
get_context_games.TOOL_SPEC = TOOL_SPEC
