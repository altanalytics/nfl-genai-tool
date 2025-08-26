import boto3
import json
import requests
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client

def test_mcp_knowledge():
    """Test just the MCP knowledge base function directly"""
    
    # Get MCP credentials
    secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
    sec_valu = secrets_client.get_secret_value(SecretId='nfl_mcp_auth')
    secret_data = json.loads(sec_valu['SecretString'])
    
    client_info = secret_data['client_info']
    CLIENT_ID = client_info['client_id']
    CLIENT_SECRET = client_info['client_secret']
    TOKEN_URL = client_info['token_endpoint']
    gateway_url = secret_data['gateway_url']
    
    print(f"Gateway URL: {gateway_url}")
    
    # Get access token
    response = requests.post(
        TOKEN_URL,
        data=f"grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}",
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    access_token = response.json()['access_token']
    print(f"Got access token: {access_token[:20]}...")
    
    # Create MCP client
    transport = streamablehttp_client(gateway_url, headers={"Authorization": f"Bearer {access_token}"})
    mcp_client = MCPClient(lambda: transport)
    
    try:
        with mcp_client:
            print("Connected to MCP client")
            
            # List tools first
            tools = []
            more_tools = True
            pagination_token = None
            while more_tools:
                tmp_tools = mcp_client.list_tools_sync(pagination_token=pagination_token)
                tools.extend(tmp_tools)
                if tmp_tools.pagination_token is None:
                    more_tools = False
                else:
                    more_tools = True 
                    pagination_token = tmp_tools.pagination_token
            
            print(f"Found tools: {[tool.tool_name for tool in tools]}")
            
            # Find the knowledge service tool
            knowledge_tool = None
            for tool in tools:
                if 'knowledge' in tool.tool_name.lower():
                    knowledge_tool = tool
                    break
            
            if not knowledge_tool:
                print("No knowledge tool found!")
                return
            
            print(f"Testing knowledge tool: {knowledge_tool.tool_name}")
            
            # Call the knowledge service directly
            import uuid
            tool_use_id = str(uuid.uuid4())
            
            result = mcp_client.call_tool_sync(
                name=knowledge_tool.tool_name,
                arguments={
                    "operation": "search_knowledge",
                    "query": "player stats table structure",
                    "max_results": 3
                },
                tool_use_id=tool_use_id
            )
            
            print("Knowledge service result:")
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_knowledge()
