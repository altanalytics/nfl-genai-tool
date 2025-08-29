import json
import boto3
import os
from datetime import datetime

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    NFL Query Learning Service - Write successful queries and learnings to S3
    """
    
    try:
        # Get environment variables
        bucket_name = os.environ.get('NFL_BUCKET', 'alt-nfl-bucket')
        
        # Parse the incoming event
        operation = event.get('operation')
        
        if operation == 'write_learning':
            return write_learning(event, bucket_name)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Unknown operation: {operation}',
                    'supported_operations': ['write_learning']
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Lambda execution error: {str(e)}'
            })
        }

def write_learning(event, bucket_name):
    """Write query learning to appropriate S3 folder"""
    
    # Extract parameters
    category = event.get('category', 'general')  # query_patterns, successful_queries, etc.
    filename = event.get('filename')
    content = event.get('content')
    
    if not filename or not content:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'filename and content are required'
            })
        }
    
    # Organize into folders as requested
    folder_mapping = {
        'player_queries': 'query_patterns/successful_player_queries',
        'team_stats': 'query_patterns/team_stats_patterns', 
        'casting_solutions': 'query_patterns/common_casting_solutions',
        'failed_queries': 'query_patterns/failed_queries_to_avoid',
        'general': 'query_patterns/general_patterns'
    }
    
    folder = folder_mapping.get(category, 'query_patterns/general_patterns')
    
    # Add timestamp to filename to avoid overwrites
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    s3_key = f"knowledge_base_query_learnings/{folder}/{timestamp}_{filename}"
    
    try:
        # Write to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content,
            ContentType='text/markdown'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': f'Learning written successfully',
                'location': f's3://{bucket_name}/{s3_key}',
                'category': category,
                'filename': filename
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'S3 write error: {str(e)}'
            })
        }
