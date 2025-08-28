# nfl_kb_search.py

import boto3
import json
from typing import Any

# NFL Knowledge Base configuration
KNOWLEDGE_BASE_ID = "DO11YJUJMC"
RETRIEVAL_CONFIG = {
    "vectorSearchConfiguration": {
        "numberOfResults": 10,
        "overrideSearchType": "SEMANTIC"
    }
}

TOOL_SPEC = {
    "name": "nfl_kb_search",
    "description": "Search NFL knowledge base for rules, statistics, and general information using semantic search.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant NFL information (e.g., 'playoff rules', 'salary cap information')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5, max: 10)",
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }
    }
}

def nfl_kb_search(tool, **kwargs: Any):
    """
    Search NFL knowledge base for rules, statistics, and general information.
    """
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]
    
    query = tool_input.get("query", "")
    max_results = tool_input.get("max_results", 5)
    
    if not query:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "Query is required for NFL knowledge base search"}]
        }
    
    if not KNOWLEDGE_BASE_ID:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "NFL Knowledge Base ID not configured"}]
        }
    
    try:
        # Create Bedrock Agent Runtime client
        bedrock_agent_client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        # Prepare retrieval configuration with custom max results
        retrieval_config = RETRIEVAL_CONFIG.copy()
        retrieval_config["vectorSearchConfiguration"]["numberOfResults"] = min(max_results, 10)
        
        # Call the retrieve API
        response = bedrock_agent_client.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={'text': query},
            retrievalConfiguration=retrieval_config
        )
        
        # Process the results
        results = []
        retrieval_results = response.get('retrievalResults', [])
        
        for result in retrieval_results:
            # Extract content, score, and location information
            content = result.get('content', {}).get('text', 'No content available')
            score = result.get('score', 0.0)
            
            # Extract location information
            location_info = result.get('location', {})
            location_type = location_info.get('type', 'UNKNOWN')
            
            # Format location based on type
            if location_type == 'S3':
                s3_location = location_info.get('s3Location', {})
                source = f"s3://{s3_location.get('uri', 'unknown')}"
            else:
                source = f"{location_type}: {location_info.get('uri', 'unknown location')}"
            
            results.append({
                'content': content,
                'relevance_score': round(score, 4),
                'source': source
            })
        
        # Format the response
        if not results:
            formatted_response = f"No relevant NFL information found for query: '{query}'"
        else:
            formatted_response = f"Found {len(results)} relevant NFL documents for query: '{query}'\n\n"
            
            for i, result in enumerate(results, 1):
                formatted_response += f"**Result {i}** (Relevance: {result['relevance_score']})\n"
                formatted_response += f"**Source:** {result['source']}\n"
                formatted_response += f"**Content:**\n{result['content']}\n"
                formatted_response += "-" * 80 + "\n\n"
        
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": [{"text": formatted_response}]
        }
        
    except bedrock_agent_client.exceptions.ResourceNotFoundException:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": f"NFL Knowledge Base not found: {KNOWLEDGE_BASE_ID}. Please check the knowledge base ID"}]
        }
    except bedrock_agent_client.exceptions.AccessDeniedException:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "Access denied to NFL knowledge base. Please check your AWS permissions for bedrock-agent-runtime:Retrieve"}]
        }
    except Exception as e:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": f"NFL knowledge base search error: {str(e)}"}]
        }
