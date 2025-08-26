"""
Direct Lambda invocation tool for NFL knowledge service
Mimics the MCP service but calls Lambda directly
"""

import boto3
import json
from strands.tools import Tool

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name='us-east-1')

def nfl_knowledge_service(operation: str, query: str, max_results: int = 5) -> str:
    """
    Search NFL knowledge base for schemas, rules, and context via direct Lambda invocation
    
    Args:
        operation: The operation to perform (should be "search_knowledge")
        query: Search terms (e.g., "player stats table structure")
        max_results: Number of results to return (1-20)
    
    Returns:
        JSON string with search results
    """
    try:
        # Prepare payload for Lambda function
        payload = {
            "operation": operation,
            "query": query,
            "max_results": max_results
        }
        
        print(f"🔧 Invoking nfl-knowledge-service Lambda with: {payload}")
        
        # Invoke Lambda function directly
        response = lambda_client.invoke(
            FunctionName='nfl-knowledge-service',
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
        print(f"❌ Error invoking nfl-knowledge-service: {e}")
        return f"Error invoking NFL knowledge service: {str(e)}"

# Create the tool
nfl_knowledge_service_tool = Tool(
    name="nfl_knowledge_service",
    description="Search NFL knowledge base for database schemas, rules, and context. Always use this first to understand table structures before writing SQL queries.",
    func=nfl_knowledge_service
)
