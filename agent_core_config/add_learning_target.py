import boto3
from bedrock_agentcore.gateway import GatewayClient

# Initialize clients
session = boto3.Session()
client = GatewayClient(session=session, region_name="us-east-1")

# Gateway and Lambda details
gateway_id = "nfl-data-gateway-g1a6zmuaqs"
lambda_arn = "arn:aws:lambda:us-east-1:175209829133:function:nfl-query-learning-service"

# Create the learning service target
learning_target_payload = {
    "lambdaArn": lambda_arn,
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

try:
    learning_target = client.create_mcp_gateway_target(
        gateway={'gatewayId': gateway_id},
        name='nfl-query-learning-service',
        target_type="lambda",
        target_payload=learning_target_payload,
        credentials=None,
    )
    print("✅ Created Lambda target: nfl-query-learning-service")
except Exception as e:
    print(f"❌ Error creating target: {e}")
