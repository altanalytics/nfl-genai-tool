# get_schedules.py

import pandas as pd
import boto3
from io import StringIO
from typing import Optional

def get_schedules(
    team1: Optional[str] = None,
    team2: Optional[str] = None, 
    season: Optional[int] = None,
    week: Optional[int] = None,
    season_type: Optional[str] = None
) -> str:
    """
    Search for NFL schedules with flexible criteria including team names, season, week, and season type.
    
    Args:
        team1: First team name in any format (case insensitive) - Washington, Commanders, WSH, etc.
        team2: Second team for head-to-head matches (optional)
        season: Season year (optional)
        week: Week number (optional)
        season_type: Season type - 'pre', 'regular', or 'post' (optional)
        
    Returns:
        str: Formatted schedule data matching the criteria
    """
    try:
        # Initialize AWS session
        s3_client = boto3.client('s3')
        s3_bucket = "alt-nfl-bucket"
        
        # Load team mapping from S3
        response = s3_client.get_object(Bucket=s3_bucket, Key="admin/team_map.csv")
        team_map = pd.read_csv(StringIO(response['Body'].read().decode('utf-8')))
        
        # Load schedule data from S3
        response = s3_client.get_object(Bucket=s3_bucket, Key="admin/clean_schedule.csv")
        schedule_df = pd.read_csv(StringIO(response['Body'].read().decode('utf-8')))
        schedule_df['date_time'] = pd.to_datetime(schedule_df['date_time'])
        schedule_df = schedule_df.sort_values('date_time', ascending=False)
        
        def find_team_abbr(team_input: str) -> Optional[str]:
            """Find team abbreviation from any team name format (case insensitive)"""
            team_input = team_input.lower()
            
            # Check team_id column
            for team_id in team_map['team_id']:
                if team_input == team_id.lower():
                    return team_id
            
            # Check team_names column
            for _, row in team_map.iterrows():
                if team_input in row['team_names'].lower():
                    return row['team_id']
            
            return None
        
        def get_season_type_code(season_type_input: str) -> Optional[int]:
            """Convert season type string to numeric code"""
            season_type_input = season_type_input.lower().strip()
            
            if season_type_input in ['pre', 'preseason', 'pre-season']:
                return 1
            elif season_type_input in ['regular', 'regular-season', 'reg']:
                return 2
            elif season_type_input in ['post', 'postseason', 'post-season', 'playoffs']:
                return 3
            
            return None
        
        # Start with full dataset
        df = schedule_df.copy()
        
        # Apply filters
        if season:
            df = df[df['season'] == season]
        
        if week:
            df = df[df['season_week'] == week]
        
        if season_type:
            season_type_code = get_season_type_code(season_type)
            if season_type_code:
                df = df[df['season_type'] == season_type_code]
        
        # Team filtering
        if team1:
            team1_abbr = find_team_abbr(team1)
            if not team1_abbr:
                return f"Could not find team '{team1}' in team mapping"
            
            if team2:
                # Head-to-head matches
                team2_abbr = find_team_abbr(team2)
                if not team2_abbr:
                    return f"Could not find team '{team2}' in team mapping"
                
                df = df[
                    ((df['home_team'] == team1_abbr) & (df['away_team'] == team2_abbr)) |
                    ((df['home_team'] == team2_abbr) & (df['away_team'] == team1_abbr))
                ]
            else:
                # Single team matches
                df = df[
                    (df['home_team'] == team1_abbr) | (df['away_team'] == team1_abbr)
                ]
        
        # Limit to 25 games max
        df = df.head(25)
        
        # Return only requested columns
        columns = ['unique_id', 'espn_id', 'matchup', 'date', 'season', 'season_name', 
                  'home_score', 'away_score', 'date_time']
        
        result_df = df[columns] if not df.empty else pd.DataFrame()
        
        # Prepare result
        num_games = len(result_df)
        
        if num_games == 0:
            return "No games found matching the specified criteria."
        else:
            result_text = f"Found {num_games} game(s) matching the criteria:\n\n"
            result_text += result_df.to_string(index=False)
            return result_text
        
    except Exception as e:
        return f"Error retrieving schedules: {str(e)}"
