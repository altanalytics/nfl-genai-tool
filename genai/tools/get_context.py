# get_context.py

import pandas as pd
import boto3
from io import StringIO
from typing import Optional

def get_context(
    unique_game_id: str,
    context: int,
    include_preseason: Optional[bool] = False
) -> str:
    """
    Get context for a specific game by returning previous games for each team and their head-to-head history.
    
    Args:
        unique_game_id: Unique game identifier (e.g., '2024_2_18_DAL_WSH')
        context: Number of previous games to return for each category
        include_preseason: Whether to include preseason games (default: false)
        
    Returns:
        str: Formatted context data with previous games for both teams and head-to-head history
    """
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
            return f"Game with ID '{unique_game_id}' not found"
        
        target_game = target_game.iloc[0]
        target_date = target_game['date_time']
        team1 = target_game['away_team']  # Away team from matchup
        team2 = target_game['home_team']  # Home team from matchup
        
        # Filter out preseason if not included
        if not include_preseason:
            filtered_df = schedule_df[schedule_df['season_type'] != 1]
        else:
            filtered_df = schedule_df.copy()
        
        # Get games before the target date
        games_before = filtered_df[filtered_df['date_time'] < target_date].sort_values('date_time', ascending=False)
        
        # Get previous games for team1 (away team)
        team1_games = games_before[
            (games_before['home_team'] == team1) | (games_before['away_team'] == team1)
        ].head(context)
        
        # Get previous games for team2 (home team)
        team2_games = games_before[
            (games_before['home_team'] == team2) | (games_before['away_team'] == team2)
        ].head(context)
        
        # Get head-to-head games (excluding games already in team1_games and team2_games)
        h2h_games = games_before[
            ((games_before['home_team'] == team1) & (games_before['away_team'] == team2)) |
            ((games_before['home_team'] == team2) & (games_before['away_team'] == team1))
        ]
        
        # Remove any h2h games that are already in the team-specific results
        team_game_ids = set(team1_games['unique_id'].tolist() + team2_games['unique_id'].tolist())
        h2h_games = h2h_games[~h2h_games['unique_id'].isin(team_game_ids)].head(context)
        
        # Return only requested columns
        columns = ['unique_id', 'espn_id', 'matchup', 'date', 'season', 'season_name', 
                  'home_score', 'away_score', 'date_time']
        
        # Prepare results
        team1_result = team1_games[columns] if not team1_games.empty else pd.DataFrame()
        team2_result = team2_games[columns] if not team2_games.empty else pd.DataFrame()
        h2h_result = h2h_games[columns] if not h2h_games.empty else pd.DataFrame()
        
        # Format output
        result_text = f"CONTEXT FOR GAME: {unique_game_id}\n"
        result_text += f"Target Game: {target_game['matchup']} on {target_game['date']}\n\n"
        
        result_text += f"AWAY TEAM ({team1}) PREVIOUS {context} GAMES:\n"
        if not team1_result.empty:
            result_text += team1_result[['date', 'matchup', 'home_score', 'away_score']].to_string(index=False)
        else:
            result_text += "No previous games found"
        result_text += "\n\n"
        
        result_text += f"HOME TEAM ({team2}) PREVIOUS {context} GAMES:\n"
        if not team2_result.empty:
            result_text += team2_result[['date', 'matchup', 'home_score', 'away_score']].to_string(index=False)
        else:
            result_text += "No previous games found"
        result_text += "\n\n"
        
        result_text += f"HEAD-TO-HEAD PREVIOUS {context} GAMES:\n"
        if not h2h_result.empty:
            result_text += h2h_result[['date', 'matchup', 'home_score', 'away_score']].to_string(index=False)
        else:
            result_text += "No previous head-to-head games found"
        
        return result_text
        
    except Exception as e:
        return f"Error retrieving game context: {str(e)}"
