import boto3
import time
import pandas as pd
from typing import Dict, Any, List


def query_athena(tool_use_id: str, sql_query: str, database: str = "nfl_stats_database") -> Dict[str, Any]:
    """
    Execute a SQL query against AWS Athena and return results.
    
    Args:
        tool_use_id: Unique identifier for this tool use
        sql_query: The SQL query to execute
        database: The Athena database name (default: nfl_stats_database)
        
    Returns:
        Dictionary with query results or error information
    """
    
    # Initialize AWS session with nfl profile
    session = boto3.Session(profile_name='nfl')
    athena_client = session.client('athena')
    s3_client = session.client('s3')
    
    # Configuration
    s3_output_bucket = "alt-nfl-bucket"
    s3_output_prefix = "athena_queries/"
    
    try:
        # Basic query validation
        sql_query = sql_query.strip()
        if not sql_query:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": "SQL query cannot be empty"}]
            }
        
        # Safety checks - only allow SELECT statements
        query_upper = sql_query.upper().strip()
        if not query_upper.startswith('SELECT'):
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": "Only SELECT queries are allowed for security reasons"}]
            }
        
        # Check for potentially dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return {
                    "toolUseId": tool_use_id,
                    "status": "error",
                    "content": [{"text": f"Query contains prohibited keyword: {keyword}"}]
                }
        
        # Start query execution
        response = athena_client.start_query_execution(
            QueryString=sql_query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={
                'OutputLocation': f's3://{s3_output_bucket}/{s3_output_prefix}'
            }
        )
        
        query_execution_id = response['QueryExecutionId']
        
        # Wait for query to complete
        max_wait_time = 60  # seconds
        wait_interval = 2   # seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            status = response['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                break
            elif status in ['FAILED', 'CANCELLED']:
                error_reason = response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                return {
                    "toolUseId": tool_use_id,
                    "status": "error",
                    "content": [{"text": f"Query failed: {error_reason}"}]
                }
            
            time.sleep(wait_interval)
            elapsed_time += wait_interval
        
        if elapsed_time >= max_wait_time:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": "Query timed out after 60 seconds"}]
            }
        
        # Get query results
        results_response = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        
        # Parse results
        result_set = results_response['ResultSet']
        rows = result_set['Rows']
        
        if not rows:
            return {
                "toolUseId": tool_use_id,
                "status": "success",
                "content": [{"text": "Query executed successfully but returned no results."}]
            }
        
        # Extract column names from first row
        columns = [col['VarCharValue'] for col in rows[0]['Data']]
        
        # Extract data rows
        data_rows = []
        for row in rows[1:]:  # Skip header row
            row_data = []
            for cell in row['Data']:
                # Handle different data types
                if 'VarCharValue' in cell:
                    row_data.append(cell['VarCharValue'])
                else:
                    row_data.append('')  # Handle null values
            data_rows.append(row_data)
        
        # Create DataFrame for better formatting
        if data_rows:
            df = pd.DataFrame(data_rows, columns=columns)
            
            # Limit results to prevent overwhelming output
            max_rows = 100
            if len(df) > max_rows:
                result_text = f"Query returned {len(df)} rows. Showing first {max_rows} rows:\n\n"
                df = df.head(max_rows)
            else:
                result_text = f"Query returned {len(df)} rows:\n\n"
            
            # Format as table
            result_text += df.to_string(index=False)
            
            # Add query execution info
            result_text += f"\n\nQuery executed successfully in {elapsed_time} seconds."
            result_text += f"\nQuery ID: {query_execution_id}"
            
        else:
            result_text = "Query executed successfully but returned no data rows."
        
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": [{"text": result_text}]
        }
        
    except Exception as e:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": f"Error executing Athena query: {str(e)}"}]
        }


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
    
    result = query_athena("test", test_query)
    
    if result["status"] == "success":
        print("SUCCESS:")
        print(result["content"][0]["text"])
    else:
        print("ERROR:")
        print(result["content"][0]["text"])


if __name__ == "__main__":
    main()
