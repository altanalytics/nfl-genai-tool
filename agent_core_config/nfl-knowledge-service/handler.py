import json
import boto3
import os

def lambda_handler(event, context):
    """
    NFL Knowledge Service MCP Handler
    Handles knowledge base searches for NFL rules, facts, and contextual information
    """
    
    # Debug logging
    print(f"DEBUG: Received event: {json.dumps(event)}")
    
    try:
        # Handle direct format from MCP Gateway
        if 'operation' in event:
            print("DEBUG: Using direct MCP Gateway format")
            result = handle_knowledge_request(event)
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
                            'name': 'nfl_knowledge_service',
                            'description': 'Search NFL knowledge base for rules, historical facts, and contextual information',
                            'inputSchema': {
                                'type': 'object',
                                'properties': {
                                    'operation': {
                                        'type': 'string',
                                        'enum': ['search_knowledge'],
                                        'description': 'The knowledge operation to perform'
                                    },
                                    'query': {
                                        'type': 'string',
                                        'description': 'The search query to find relevant information'
                                    },
                                    'max_results': {
                                        'type': 'integer',
                                        'description': 'Maximum number of results to return (default: 10, max: 20)',
                                        'minimum': 1,
                                        'maximum': 20,
                                        'default': 10
                                    }
                                },
                                'required': ['operation', 'query']
                            }
                        }
                    ]
                })
            }
        
        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            
            if tool_name == 'nfl_knowledge_service':
                result = handle_knowledge_request(arguments)
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

def handle_knowledge_request(request):
    """Handle the actual knowledge base request"""
    operation = request.get('operation')
    
    if operation == 'search_knowledge':
        return search_knowledge_base(request)
    else:
        return {'error': f'Unknown operation: {operation}'}

def search_knowledge_base(request):
    """Search the knowledge base for relevant information"""
    query = request.get('query', '').strip()
    max_results = request.get('max_results', 10)
    
    if not query:
        return {'error': 'Query is required for knowledge base search'}
    
    # Get knowledge base ID from environment variable
    knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID')
    if not knowledge_base_id:
        return {'error': 'Knowledge base ID not configured'}
    
    try:
        # Initialize Bedrock Agent Runtime client
        bedrock_agent_client = boto3.client('bedrock-agent-runtime')
        
        # Configure retrieval parameters
        retrieval_config = {
            "vectorSearchConfiguration": {
                "numberOfResults": min(max_results, 20),
                "overrideSearchType": "SEMANTIC"
            }
        }
        
        # Execute the knowledge base query
        response = bedrock_agent_client.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={
                'text': query
            },
            retrievalConfiguration=retrieval_config
        )
        
        # Process the results
        results = []
        for result in response.get('retrievalResults', []):
            content = result.get('content', {})
            location = result.get('location', {})
            score = result.get('score', 0)
            
            # Extract relevant information
            result_data = {
                'content': content.get('text', ''),
                'score': score,
                'source': location.get('s3Location', {}).get('uri', 'Unknown source')
            }
            
            # Add metadata if available
            if 'metadata' in result:
                result_data['metadata'] = result['metadata']
            
            results.append(result_data)
        
        return {
            'success': True,
            'query': query,
            'results_count': len(results),
            'max_results': max_results,
            'results': results
        }
        
    except Exception as e:
        return {'error': f'Error searching knowledge base: {str(e)}'}
