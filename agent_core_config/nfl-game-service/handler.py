import json
import boto3
import os

def lambda_handler(event, context):
    """
    NFL Game Service MCP Handler
    Handles retrieval of complete game data (inputs and outputs) from S3
    """
    
    # Debug logging
    print(f"DEBUG: Received event: {json.dumps(event)}")
    
    try:
        # Handle direct format from MCP Gateway
        if 'operation' in event:
            print("DEBUG: Using direct MCP Gateway format")
            result = handle_game_request(event)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'content': [{'type': 'text', 'text': json.dumps(result, indent=2)}]
                })
            }
        
        # Handle MCP Protocol format for direct testing
        body = json.loads(event.get('body', '{}'))
        method = body.get('method')
        params = body.get('params', {})
        
        print(f"DEBUG: Method: {method}, Params: {params}")
        
        if method == 'tools/list':
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'tools': [
                        {
                            'name': 'nfl_game_service',
                            'description': 'Retrieve complete game data including inputs and outputs for specific NFL games',
                            'inputSchema': {
                                'type': 'object',
                                'properties': {
                                    'operation': {
                                        'type': 'string',
                                        'enum': ['get_game_details'],
                                        'description': 'The game operation to perform'
                                    },
                                    'game_id': {
                                        'type': 'string',
                                        'description': 'The unique game ID (e.g., "2024_2_08_WSH_CHI")'
                                    },
                                    'include_inputs': {
                                        'type': 'boolean',
                                        'description': 'Whether to include input data files (default: true)',
                                        'default': True
                                    },
                                    'include_outputs': {
                                        'type': 'boolean',
                                        'description': 'Whether to include output data files (default: true)',
                                        'default': True
                                    }
                                },
                                'required': ['operation', 'game_id']
                            }
                        }
                    ]
                })
            }
        
        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            
            if tool_name == 'nfl_game_service':
                result = handle_game_request(arguments)
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'content': [{'type': 'text', 'text': json.dumps(result, indent=2)}]
                    })
                }
        
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Unsupported method'})
        }
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_game_request(request):
    """Handle the actual game data request"""
    operation = request.get('operation')
    
    if operation == 'get_game_details':
        return get_game_details(request)
    else:
        return {'error': f'Unknown operation: {operation}'}

def get_game_details(request):
    """Retrieve complete game data from S3"""
    game_id = request.get('game_id', '').strip()
    include_inputs = request.get('include_inputs', True)
    include_outputs = request.get('include_outputs', True)
    
    if not game_id:
        return {'error': 'Game ID is required'}
    
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        s3_bucket = "alt-nfl-bucket"
        
        # Parse the unique_game_id to construct S3 path
        parts = game_id.split('_')
        if len(parts) < 4:
            return {'error': f'Invalid game ID format: {game_id}. Expected format: YYYY_T_WW_TEAM1_TEAM2'}
        
        season = parts[0]  # e.g., "2024"
        season_type_code = parts[1]  # e.g., "2"
        week = parts[2]  # e.g., "08"
        
        # Map season type code to folder name
        season_type_map = {
            "1": "preseason",
            "2": "regular-season", 
            "3": "postseason"
        }
        
        season_type_folder = season_type_map.get(season_type_code)
        if not season_type_folder:
            return {'error': f'Invalid season type code: {season_type_code}'}
        
        # Construct base S3 path
        week_padded = week.zfill(2)  # Ensure 2-digit week
        base_path = f"nfl_espn_data/season_{season}/{season_type_folder}/week_{week_padded}/{game_id}"
        
        game_data = {
            'game_id': game_id,
            'season': season,
            'season_type': season_type_folder,
            'week': week,
            'inputs': {},
            'outputs': {}
        }
        
        # Get input files if requested
        if include_inputs:
            inputs_path = f"{base_path}/inputs/"
            try:
                response = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=inputs_path)
                if 'Contents' in response:
                    for obj in response['Contents']:
                        file_key = obj['Key']
                        filename = file_key.split('/')[-1]
                        
                        if filename:  # Skip directory entries
                            try:
                                file_response = s3_client.get_object(Bucket=s3_bucket, Key=file_key)
                                file_content = file_response['Body'].read().decode('utf-8')
                                
                                # Try to parse as JSON
                                try:
                                    game_data['inputs'][filename] = json.loads(file_content)
                                except json.JSONDecodeError:
                                    # Store as string if not JSON
                                    game_data['inputs'][filename] = file_content
                                    
                            except Exception as e:
                                game_data['inputs'][filename] = {'error': f'Failed to read file: {str(e)}'}
                else:
                    game_data['inputs'] = {'message': 'No input files found'}
            except Exception as e:
                game_data['inputs'] = {'error': f'Failed to access inputs: {str(e)}'}
        
        # Get output files if requested
        if include_outputs:
            outputs_path = f"{base_path}/outputs/"
            try:
                response = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=outputs_path)
                if 'Contents' in response:
                    for obj in response['Contents']:
                        file_key = obj['Key']
                        filename = file_key.split('/')[-1]
                        
                        if filename:  # Skip directory entries
                            try:
                                file_response = s3_client.get_object(Bucket=s3_bucket, Key=file_key)
                                file_content = file_response['Body'].read().decode('utf-8')
                                
                                # Try to parse as JSON
                                try:
                                    game_data['outputs'][filename] = json.loads(file_content)
                                except json.JSONDecodeError:
                                    # Store as string if not JSON
                                    game_data['outputs'][filename] = file_content
                                    
                            except Exception as e:
                                game_data['outputs'][filename] = {'error': f'Failed to read file: {str(e)}'}
                else:
                    game_data['outputs'] = {'message': 'No output files found'}
            except Exception as e:
                game_data['outputs'] = {'error': f'Failed to access outputs: {str(e)}'}
        
        # Add metadata
        input_count = len([k for k in game_data['inputs'].keys() if not k.startswith('_')])
        output_count = len([k for k in game_data['outputs'].keys() if not k.startswith('_')])
        
        game_data['metadata'] = {
            'base_s3_path': f's3://{s3_bucket}/{base_path}',
            'input_files_found': input_count,
            'output_files_found': output_count,
            'included_inputs': include_inputs,
            'included_outputs': include_outputs
        }
        
        return {
            'success': True,
            'data': game_data
        }
        
    except Exception as e:
        return {'error': f'Error retrieving game data: {str(e)}'}
