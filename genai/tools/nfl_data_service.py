"""
Direct Lambda invocation tool for NFL data service
Mimics the MCP service but calls Lambda directly
"""

import boto3
import json
from strands.tools import Tool

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name='us-east-1')

def nfl_data_service(operation: str, sql: str = None, database: str = "nfl_stats_database") -> str:
    """
    Execute SQL queries against the NFL Athena database via direct Lambda invocation
    
    Args:
        operation: The operation to perform (should be "query_database")
        sql: The SQL SELECT statement to execute
        database: The database name (default: nfl_stats_database)
    
    Returns:
        JSON string with query results
    """
    try:
        # Prepare payload for Lambda function
        payload = {
            "operation": operation,
            "sql": sql,
            "database": database
        }
        
        print(f"🔧 Invoking nfl-data-service Lambda with: {payload}")
        
        # Invoke Lambda function directly
        response = lambda_client.invoke(
            FunctionName='nfl-data-service',
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
        print(f"❌ Error invoking nfl-data-service: {e}")
        return f"Error invoking NFL data service: {str(e)}"

# Create the tool
nfl_data_service_tool = Tool(
    name="nfl_data_service",
    description="Execute SQL queries against the NFL Athena database. Use this for statistical analysis and data retrieval.",
    func=nfl_data_service
)
