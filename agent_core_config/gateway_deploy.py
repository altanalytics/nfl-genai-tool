#!/usr/bin/env python3
"""
NFL MCP Gateway Deploy - Initial MCP Gateway Setup
Creates Cognito resources, MCP gateway, and initial Lambda targets
Run this ONCE for initial setup
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
    functions = ['nfl-data-service', 'nfl-game-service', 'nfl-knowledge-service', 'nfl-query-learning-service']
    
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

def main():
    # Check for AWS credentials
    if not os.environ.get('AWS_PROFILE') and not os.environ.get('AWS_ACCESS_KEY_ID'):
        print("❌ AWS credentials not found!")
        print("Please set AWS_PROFILE environment variable:")
        print("   AWS_PROFILE=your-profile-name uv run gateway_deploy.py")
        return

    # Check if gateway already exists
    secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
    
    try:
        secrets_client.get_secret_value(SecretId='nfl_mcp_auth')
        print("⚠️  NFL MCP Gateway already exists!")
        print("Use gateway_update.py to update existing gateway")
        print("Or delete the 'nfl_mcp_auth' secret to start fresh")
        return
    except secrets_client.exceptions.ResourceNotFoundException:
        pass  # Good, no existing gateway
    
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
    
    print("🔧 Creating Cognito resources...")
    
    # Create cognito authorizer
    cognito_response = client.create_oauth_authorizer_with_cognito("NFL_Data_Auth")
    
    print("🔧 Creating MCP Gateway...")
    
    # Create the gateway
    gateway = client.create_mcp_gateway(
        name='NFL-Data-Gateway',
        role_arn=None,  # Let it create the role
        authorizer_config=cognito_response["authorizer_config"],
        enable_semantic_search=True,
    )
    
    print("🔧 Saving configuration to Secrets Manager...")
    
    # Save to secrets manager
    secrets_client.create_secret(
        Name='nfl_mcp_auth',
        SecretString=json.dumps({
            "authorizer_config": cognito_response["authorizer_config"],
            "client_info": cognito_response["client_info"],
            "gateway_id": gateway['gatewayId'],
            "gateway_url": gateway['gatewayUrl'],
        })
    )
    
    print("🔧 Creating Lambda targets...")
    
    # Create NFL Data Service target (Athena queries)
    data_target_payload = {
        "lambdaArn": lambda_arns['nfl-data-service'],
        "toolSchema": {
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
    }
    
    # Create NFL Game Service target (Game data retrieval)
    game_target_payload = {
        "lambdaArn": lambda_arns['nfl-game-service'],
        "toolSchema": {
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
    }
    
    # Create NFL Knowledge Service target (Knowledge base search)
    knowledge_target_payload = {
        "lambdaArn": lambda_arns['nfl-knowledge-service'],
        "toolSchema": {
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
    
    # Create NFL Query Learning Service target (Write learnings to S3)
    learning_target_payload = {
        "lambdaArn": lambda_arns['nfl-query-learning-service'],
        "toolSchema": {
            "inlinePayload": [
                {
                    "name": "nfl_query_learning_service",
                    "description": "Write successful query patterns and learnings to S3 for knowledge base",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "description": "The operation to perform (use 'write_learning')"
                            },
                            "category": {
                                "type": "string",
                                "description": "Category: player_queries, team_stats, casting_solutions, failed_queries, or general"
                            },
                            "filename": {
                                "type": "string",
                                "description": "Filename for the learning document (e.g., 'jayden_daniels_passing_pattern.md')"
                            },
                            "content": {
                                "type": "string",
                                "description": "Markdown content with query pattern, SQL, and learnings"
                            }
                        },
                        "required": ["operation", "filename", "content"]
                    }
                }
            ]
        }
    }
    
    # Create all targets
    try:
        data_target = client.create_mcp_gateway_target(
            gateway=gateway,
            name='nfl-data-service',
            target_type="lambda",
            target_payload=data_target_payload,
            credentials=None,
        )
        print("✅ Created Lambda target: nfl-data-service")
        
        game_target = client.create_mcp_gateway_target(
            gateway=gateway,
            name='nfl-game-service',
            target_type="lambda",
            target_payload=game_target_payload,
            credentials=None,
        )
        print("✅ Created Lambda target: nfl-game-service")
        
        knowledge_target = client.create_mcp_gateway_target(
            gateway=gateway,
            name='nfl-knowledge-service',
            target_type="lambda",
            target_payload=knowledge_target_payload,
            credentials=None,
        )
        print("✅ Created Lambda target: nfl-knowledge-service")
        
        learning_target = client.create_mcp_gateway_target(
            gateway=gateway,
            name='nfl-query-learning-service',
            target_type="lambda",
            target_payload=learning_target_payload,
            credentials=None,
        )
        print("✅ Created Lambda target: nfl-query-learning-service")
        
    except Exception as e:
        print(f"⚠️  Error creating Lambda targets: {e}")
        print("You can create them later with gateway_update.py")
    
    print(f"\n🎉 NFL MCP Gateway deployment complete!")
    print(f"Gateway ID: {gateway['gatewayId']}")
    print(f"Gateway URL: {gateway['gatewayUrl']}")
    print(f"Lambda ARNs:")
    for name, arn in lambda_arns.items():
        print(f"  {name}: {arn}")
    print(f"\n📝 Next steps:")
    print("1. Test with: AWS_PROFILE=your-profile uv run test_mcp_gateway.py")
    print("2. Use gateway_update.py for future updates")
    print("3. Update your agent configuration with the gateway URL")

if __name__ == "__main__":
    main()
