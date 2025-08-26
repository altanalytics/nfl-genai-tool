#!/usr/bin/env python3
"""
NFL MCP Gateway Update - Update existing MCP Gateway targets
Updates Lambda targets on existing gateway
Run this for updates after initial deployment
"""

import boto3
import json
import os
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import logging

def get_lambda_arns():
    """Dynamically discover all NFL Lambda ARNs"""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    arns = {}
    functions = ['nfl-data-service', 'nfl-game-service', 'nfl-knowledge-service']
    
    for func_name in functions:
        try:
            response = lambda_client.get_function(FunctionName=func_name)
            arns[func_name] = response['Configuration']['FunctionArn']
            print(f"✅ Found {func_name}: {arns[func_name]}")
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"❌ Lambda function '{func_name}' not found!")
            print("Please run deploy_lambdas.py first")
            return None
    
    return arns

def get_gateway_config():
    """Get existing gateway configuration from Secrets Manager"""
    secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
    
    try:
        response = secrets_client.get_secret_value(SecretId='nfl_mcp_auth')
        config = json.loads(response['SecretString'])
        print(f"✅ Found existing gateway: {config['gateway_id']}")
        return config
    except secrets_client.exceptions.ResourceNotFoundException:
        print("❌ No existing NFL MCP Gateway found!")
        print("Please run gateway_deploy.py first")
        return None

def main():
    # Check for AWS credentials
    if not os.environ.get('AWS_PROFILE') and not os.environ.get('AWS_ACCESS_KEY_ID'):
        print("❌ AWS credentials not found!")
        print("Please set AWS_PROFILE environment variable:")
        print("   AWS_PROFILE=your-profile-name uv run gateway_update.py")
        return

    # Get existing gateway configuration
    gateway_config = get_gateway_config()
    if not gateway_config:
        return
    
    # Get Lambda ARNs
    lambda_arns = get_lambda_arns()
    if not lambda_arns:
        return
    
    print(f"✅ Found Lambda functions:")
    for name, arn in lambda_arns.items():
        print(f"   {name}: {arn}")
    
    # Setup the client
    client = GatewayClient(region_name="us-east-1")
    client.logger.setLevel(logging.INFO)
    
    # Reconstruct gateway object
    gateway = {
        'gatewayId': gateway_config['gateway_id'],
        'gatewayUrl': gateway_config['gateway_url']
    }
    
    print("🔧 Updating Lambda targets...")
    
    # Define target configurations
    targets = [
        {
            'name': 'nfl-data-service',
            'lambda_arn': lambda_arns['nfl-data-service'],
            'tool_schema': {
                "inlinePayload": [
                    {
                        "name": "nfl_data_service",
                        "description": "Execute SQL queries against the NFL Athena database for statistical analysis",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "operation": {
                                    "type": "string",
                                    "description": "The data operation to perform (use 'query_database')"
                                },
                                "sql": {
                                    "type": "string",
                                    "description": "The SQL query to execute (SELECT statements only)"
                                },
                                "database": {
                                    "type": "string",
                                    "description": "The database name (use 'nfl_stats_database')"
                                }
                            },
                            "required": ["operation", "sql"]
                        }
                    }
                ]
            }
        },
        {
            'name': 'nfl-game-service',
            'lambda_arn': lambda_arns['nfl-game-service'],
            'tool_schema': {
                "inlinePayload": [
                    {
                        "name": "nfl_game_service",
                        "description": "Retrieve complete game data including inputs and outputs for specific NFL games",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "operation": {
                                    "type": "string",
                                    "description": "The game operation to perform (use 'get_game_details')"
                                },
                                "game_id": {
                                    "type": "string",
                                    "description": "The unique game ID (e.g., '2024_2_08_WSH_CHI')"
                                },
                                "include_inputs": {
                                    "type": "boolean",
                                    "description": "Whether to include input data files"
                                },
                                "include_outputs": {
                                    "type": "boolean",
                                    "description": "Whether to include output data files"
                                }
                            },
                            "required": ["operation", "game_id"]
                        }
                    }
                ]
            }
        },
        {
            'name': 'nfl-knowledge-service',
            'lambda_arn': lambda_arns['nfl-knowledge-service'],
            'tool_schema': {
                "inlinePayload": [
                    {
                        "name": "nfl_knowledge_service",
                        "description": "Search NFL knowledge base for rules, historical facts, and contextual information",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "operation": {
                                    "type": "string",
                                    "description": "The knowledge operation to perform (use 'search_knowledge')"
                                },
                                "query": {
                                    "type": "string",
                                    "description": "The search query to find relevant information"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return (1-20)"
                                }
                            },
                            "required": ["operation", "query"]
                        }
                    }
                ]
            }
        }
    ]
    
    # Update each target
    updated_targets = []
    for target_config in targets:
        try:
            target_payload = {
                "lambdaArn": target_config['lambda_arn'],
                "toolSchema": target_config['tool_schema']
            }
            
            # Try to update existing target, or create if it doesn't exist
            try:
                target = client.update_mcp_gateway_target(
                    gateway=gateway,
                    name=target_config['name'],
                    target_type="lambda",
                    target_payload=target_payload,
                    credentials=None,
                )
                print(f"✅ Updated Lambda target: {target_config['name']}")
            except Exception as update_error:
                print(f"⚠️  Update failed for {target_config['name']}, trying to create: {update_error}")
                target = client.create_mcp_gateway_target(
                    gateway=gateway,
                    name=target_config['name'],
                    target_type="lambda",
                    target_payload=target_payload,
                    credentials=None,
                )
                print(f"✅ Created Lambda target: {target_config['name']}")
            
            updated_targets.append(target_config['name'])
            
        except Exception as e:
            print(f"❌ Error with target {target_config['name']}: {e}")
    
    print(f"\n🎉 Gateway update complete!")
    print(f"Gateway ID: {gateway_config['gateway_id']}")
    print(f"Gateway URL: {gateway_config['gateway_url']}")
    print(f"Updated targets: {', '.join(updated_targets)}")
    print(f"\n📝 Next steps:")
    print("1. Test with: AWS_PROFILE=your-profile uv run test_mcp_gateway.py")

if __name__ == "__main__":
    main()
