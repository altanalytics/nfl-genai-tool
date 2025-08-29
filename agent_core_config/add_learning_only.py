import boto3

# Use bedrock-agentcore-control client directly
client = boto3.client('bedrock-agentcore-control', region_name='us-east-1')

gateway_id = "nfl-data-gateway-g1a6zmuaqs"
lambda_arn = "arn:aws:lambda:us-east-1:175209829133:function:nfl-query-learning-service"

try:
    response = client.create_gateway_target(
        gatewayIdentifier=gateway_id,
        name='nfl-query-learning-service',
        targetConfiguration={
            'mcp': {
                'lambda': {
                    'lambdaArn': lambda_arn,
                    'toolSchema': {
                        'inlinePayload': [
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
                                            "description": "Filename for the learning document"
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
            }
        },
        credentialProviderConfigurations=[
            {
                'credentialProviderType': 'GATEWAY_IAM_ROLE'
            }
        ]
    )
    print("✅ Successfully added nfl-query-learning-service target")
    print(f"Target ID: {response.get('targetId', 'N/A')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
