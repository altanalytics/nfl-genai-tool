import json
import boto3
import time
# import pandas as pd  # Removed to avoid Lambda import issues
import os

def lambda_handler(event, context):
    """
    NFL Data Service MCP Handler
    Handles Athena database queries for NFL statistics and analysis
    """
    
    # Debug logging
    print(f"DEBUG: Received event: {json.dumps(event)}")
    
    try:
        # Handle direct format from MCP Gateway
        if 'operation' in event:
            print("DEBUG: Using direct MCP Gateway format")
            result = handle_data_request(event)
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
                            'name': 'nfl_data_service',
                            'description': 'Execute SQL queries against the NFL Athena database for statistical analysis',
                            'inputSchema': {
                                'type': 'object',
                                'properties': {
                                    'operation': {
                                        'type': 'string',
                                        'enum': ['query_database'],
                                        'description': 'The data operation to perform'
                                    },
                                    'sql': {
                                        'type': 'string',
                                        'description': 'The SQL query to execute (SELECT statements only)'
                                    },
                                    'database': {
                                        'type': 'string',
                                        'description': 'The database name (default: nfl_stats_database)',
                                        'default': 'nfl_stats_database'
                                    }
                                },
                                'required': ['operation', 'sql']
                            }
                        }
                    ]
                })
            }
        
        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            
            if tool_name == 'nfl_data_service':
                result = handle_data_request(arguments)
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

def handle_data_request(request):
    """Handle the actual data request"""
    operation = request.get('operation')
    
    if operation == 'query_database':
        return execute_athena_query(request)
    else:
        return {'error': f'Unknown operation: {operation}'}

def execute_athena_query(request):
    """Execute SQL query against Athena database"""
    sql_query = request.get('sql', '').strip()
    database = request.get('database', 'nfl_stats_database')
    
    if not sql_query:
        return {'error': 'SQL query is required'}
    
    # Safety checks - only allow SELECT statements
    query_upper = sql_query.upper().strip()
    if not query_upper.startswith('SELECT'):
        return {'error': 'Only SELECT queries are allowed for security reasons'}
    
    # Check for potentially dangerous keywords
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'TRUNCATE']
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return {'error': f'Query contains prohibited keyword: {keyword}'}
    
    try:
        # Initialize Athena client
        athena_client = boto3.client('athena')
        
        # Configuration
        s3_output_bucket = "alt-nfl-bucket"
        s3_output_prefix = "athena_queries/"
        
        # Start query execution
        response = athena_client.start_query_execution(
            QueryString=sql_query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={
                'OutputLocation': f's3://{s3_output_bucket}/{s3_output_prefix}'
            },
            WorkGroup='primary'
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
                return {'error': f'Query failed: {error_reason}'}
            
            time.sleep(wait_interval)
            elapsed_time += wait_interval
        
        if elapsed_time >= max_wait_time:
            return {'error': 'Query timed out after 60 seconds'}
        
        # Get query results
        results_response = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        
        # Parse results
        result_set = results_response['ResultSet']
        rows = result_set['Rows']
        
        if not rows:
            return {
                'success': True,
                'message': 'Query executed successfully but returned no results',
                'query_id': query_execution_id,
                'execution_time': elapsed_time
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
        
        # Create formatted data structure without pandas
        if data_rows:
            # Limit results to prevent overwhelming output
            max_rows = 100
            if len(data_rows) > max_rows:
                result_message = f"Query returned {len(data_rows)} rows. Showing first {max_rows} rows."
                limited_rows = data_rows[:max_rows]
            else:
                result_message = f"Query returned {len(data_rows)} rows."
                limited_rows = data_rows
            
            # Convert to list of dictionaries for JSON serialization
            result_data = []
            for row in limited_rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = row[i] if i < len(row) else None
                result_data.append(row_dict)
            
            return {
                'success': True,
                'message': result_message,
                'columns': columns,
                'data': result_data,
                'row_count': len(data_rows),
                'query_id': query_execution_id,
                'execution_time': elapsed_time
            }
        else:
            return {
                'success': True,
                'message': 'Query executed successfully but returned no data rows',
                'query_id': query_execution_id,
                'execution_time': elapsed_time
            }
            
    except Exception as e:
        return {'error': f'Error executing Athena query: {str(e)}'}
