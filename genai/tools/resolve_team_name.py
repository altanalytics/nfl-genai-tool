# resolve_team_name.py

import pandas as pd
import boto3
from io import StringIO
from typing import Any, Optional

# 1. Tool Specification
TOOL_SPEC = {
    "name": "resolve_team_name",
    "description": "Resolve team name variants (full names, cities, abbreviations) to standardized team_id using the team mapping data.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "Team name, city, abbreviation, or any variant to resolve to team_id (e.g., 'Patriots', 'New England', 'NE', 'Kansas City Chiefs', 'KC')"
                }
            },
            "required": ["team_name"]
        }
    }
}

# 2. Tool Function
def resolve_team_name(tool, **kwargs: Any):
    """
    Resolves a team name variant to the standardized team_id.
    
    Args:
        tool: Tool object containing toolUseId and input parameters
        **kwargs: Additional keyword arguments
        
    Returns:
        dict: Structured response with team_id or error message
    """
    # Extract tool parameters
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]
    
    team_name = tool_input.get("team_name", "").strip()
    
    if not team_name:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "Team name is required"}]
        }
    
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Download team mapping CSV from S3
        bucket_name = 'alt-nfl-bucket'
        key = 'nfl_data/team_map.csv'
        
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        
        # Read into pandas DataFrame
        df = pd.read_csv(StringIO(csv_content))
        
        # Search for team name match (case-insensitive)
        team_name_lower = team_name.lower()
        
        # Check each row's team_names field for a match
        matched_team_id = None
        matched_variants = None
        
        for _, row in df.iterrows():
            team_id = row['team_id']
            team_names_str = str(row['team_names']).lower()
            
            # Split team_names by spaces and check for matches
            name_variants = team_names_str.split()
            
            # Check if the input matches any variant (exact match or contains)
            for variant in name_variants:
                if (team_name_lower == variant or 
                    team_name_lower in variant or 
                    variant in team_name_lower):
                    matched_team_id = team_id
                    matched_variants = row['team_names']
                    break
            
            if matched_team_id:
                break
        
        # If no exact match found, try partial matching on full team_names string
        if not matched_team_id:
            for _, row in df.iterrows():
                team_id = row['team_id']
                team_names_str = str(row['team_names']).lower()
                
                if team_name_lower in team_names_str:
                    matched_team_id = team_id
                    matched_variants = row['team_names']
                    break
        
        if matched_team_id:
            result_text = f"✅ Team resolved successfully!\n"
            result_text += f"Input: '{team_name}'\n"
            result_text += f"Team ID: {matched_team_id}\n"
            result_text += f"Available variants: {matched_variants}"
            
            return {
                "toolUseId": tool_use_id,
                "status": "success",
                "team_id": matched_team_id,
                "content": [{"text": result_text}]
            }
        else:
            # Show available teams for reference
            available_teams = "\n".join([f"{row['team_id']}: {row['team_names']}" for _, row in df.iterrows()])
            
            result_text = f"❌ No match found for '{team_name}'\n\n"
            result_text += f"Available teams and their variants:\n{available_teams}\n\n"
            result_text += f"Try using team city, full name, or abbreviation (e.g., 'Patriots', 'New England', 'NE')"
            
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": result_text}]
            }
        
    except Exception as e:
        error_message = f"Error resolving team name: {str(e)}"
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": error_message}]
        }

# Attach TOOL_SPEC to function for Strands framework
resolve_team_name.TOOL_SPEC = TOOL_SPEC
