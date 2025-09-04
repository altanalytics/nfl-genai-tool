"""
Direct Lambda invocation tool for NFL game service
Mimics the MCP service but calls Lambda directly
"""

import boto3
import json

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name='us-east-1')

TOOL_SPEC = {
    "name": "nfl_game_service",
    "description": "Retrieve complete game data and analysis including play-by-play, stats, and existing recaps.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The operation to perform (should be 'get_game_details')"
                },
                "game_id": {
                    "type": "string", 
                    "description": "Game identifier (e.g., '2024_2_08_WSH_CHI')"
                },
                "include_inputs": {
                    "type": "boolean",
                    "description": "Whether to include game input data",
                    "default": True
                },
                "include_outputs": {
                    "type": "boolean", 
                    "description": "Whether to include game output data",
                    "default": True
                }
            },
            "required": ["operation", "game_id"]
        }
    }
}

def nfl_game_service(operation: str, game_id: str, include_inputs: bool = True, include_outputs: bool = True) -> str:
    """
    Retrieve complete game data and analysis via direct Lambda invocation
    
    Args:
        operation: The operation to perform (should be "get_game_details")
        game_id: Game identifier (e.g., "2024_2_08_WSH_CHI")
        include_inputs: Whether to include game input data
        include_outputs: Whether to include game output data
    
    Returns:
        JSON string with game data
    """
    try:
        # Prepare payload for Lambda function
        payload = {
            "operation": operation,
            "game_id": game_id,
            "include_inputs": include_inputs,
            "include_outputs": include_outputs
        }
        
        print(f"🔧 Invoking nfl-game-service Lambda with: {payload}")
        
        # Invoke Lambda function directly
        response = lambda_client.invoke(
            FunctionName='nfl-game-service',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"🔧 Lambda response: {response_payload}")
        
        if response.get('StatusCode') == 200:
            return json.dumps(response_payload, indent=2)
        else:
            return f"Error: Lambda returned status {response.get('StatusCode')}: {response_payload}"
            
    except Exception as e:
        print(f"❌ Error invoking nfl-game-service: {e}")
        return f"Error invoking NFL game service: {str(e)}"
