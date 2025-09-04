import boto3
import time
import pandas as pd
from typing import Dict, Any, List

TOOL_SPEC = {
    "name": "query_athena",
    "description": "Execute SQL queries against the NFL statistics database using AWS Athena. Only SELECT queries are allowed.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "The SQL query to execute (SELECT statements only)"
                },
                "database": {
                    "type": "string", 
                    "description": "The Athena database name",
                    "default": "nfl_stats_database"
                }
            },
            "required": ["sql_query"]
        }
    }
}

def query_athena(sql_query: str, database: str = "nfl_stats_database") -> str:
    """
    Execute a SQL query against AWS Athena and return results.
    
    Args:
        sql_query: The SQL query to execute
        database: The Athena database name (default: nfl_stats_database)
        
    Returns:
        String with query results or error information
    """
    
    # Initialize AWS session with nfl profile
    session = boto3.Session(profile_name='nfl')
    athena_client = session.client('athena')
    
    # Configuration
    s3_output_bucket = "alt-nfl-bucket"
    s3_output_prefix = "athena_queries/"
    
    try:
        # Basic query validation
        sql_query = sql_query.strip()
        if not sql_query:
            return "Error: SQL query cannot be empty"
        
        # Safety checks - only allow SELECT statements
        query_upper = sql_query.upper().strip()
        if not query_upper.startswith('SELECT'):
            return "Error: Only SELECT queries are allowed for security reasons"
        
        # Check for potentially dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return f"Error: Query contains forbidden keyword '{keyword}'. Only SELECT queries are allowed."
        
        # Start query execution
        response = athena_client.start_query_execution(
            QueryString=sql_query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={
                'OutputLocation': f's3://{s3_output_bucket}/{s3_output_prefix}'
            }
        )
        
        query_execution_id = response['QueryExecutionId']
        
        # Wait for query completion
        max_wait_time = 60  # seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            status = response['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                break
            elif status in ['FAILED', 'CANCELLED']:
                error_reason = response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                return f"Error: Query failed - {error_reason}"
            
            time.sleep(2)
            elapsed_time += 2
        
        if elapsed_time >= max_wait_time:
            return "Error: Query timed out after 60 seconds"
        
        # Get query results
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        
        # Process results
        rows = results['ResultSet']['Rows']
        
        if not rows:
            return "Query executed successfully but returned no data rows."
        
        # Extract column names from first row
        columns = [col['VarCharValue'] for col in rows[0]['Data']]
        
        # Extract data rows (skip header)
        data_rows = []
        for row in rows[1:]:  # Skip header row
            row_data = []
            for cell in row['Data']:
                # Handle different data types
                if 'VarCharValue' in cell:
                    row_data.append(cell['VarCharValue'])
                elif 'BigIntValue' in cell:
                    row_data.append(str(cell['BigIntValue']))
                elif 'IntegerValue' in cell:
                    row_data.append(str(cell['IntegerValue']))
                elif 'DoubleValue' in cell:
                    row_data.append(str(cell['DoubleValue']))
                else:
                    row_data.append('NULL')
            data_rows.append(row_data)
        
        # Format results as a readable table
        if data_rows:
            # Create DataFrame for better formatting
            df = pd.DataFrame(data_rows, columns=columns)
            result_text = f"Query Results ({len(data_rows)} rows):\n\n{df.to_string(index=False)}"
        else:
            result_text = "Query executed successfully but returned no data rows."
        
        return result_text
        
    except Exception as e:
        return f"Error executing Athena query: {str(e)}"


def main():
    """Example usage"""
    # Test query
    test_query = """
    SELECT season, COUNT(*) as game_count 
    FROM clean_schedule 
    WHERE season = 2024 
    GROUP BY season
    """
    
    print("=== TESTING ATHENA QUERY ===")
    print(f"Query: {test_query}")
    
    result = query_athena(test_query)
    print("Result:")
    print(result)


if __name__ == "__main__":
    main()
