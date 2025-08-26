from agent_config import create_strands_agent
import logging
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client 
import os
import requests
import json
import boto3
import time

# NFL MCP Configuration
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
sec_valu = secrets_client.get_secret_value(SecretId='nfl_mcp_auth')
client_info = json.loads(sec_valu['SecretString'])['client_info']
CLIENT_ID = client_info['client_id']
CLIENT_SECRET = client_info['client_secret']
TOKEN_URL = client_info['token_endpoint']
gateway_url = json.loads(sec_valu['SecretString'])['gateway_url']


def fetch_access_token(client_id, client_secret, token_url):
    response = requests.post(
        token_url,
        data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    return response.json()['access_token']

def create_streamable_http_transport(mcp_url: str, access_token: str):
    return streamablehttp_client(mcp_url, headers={"Authorization": f"Bearer {access_token}"})


def get_full_tools_list(client):
    """
    List tools w/ support for pagination
    """
    more_tools = True
    tools = []
    pagination_token = None
    while more_tools:
        tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
        tools.extend(tmp_tools)
        if tmp_tools.pagination_token is None:
            more_tools = False
        else:
            more_tools = True 
            pagination_token = tmp_tools.pagination_token
    return tools

def run_agent_with_retry(mcp_url: str, access_token: str, user_input: str, max_retries: int = 2):
    """Run agent with retry logic for connection issues"""
    for attempt in range(max_retries + 1):
        try:
            mcp_client = MCPClient(lambda: create_streamable_http_transport(mcp_url, access_token))
            
            with mcp_client:
                tools = get_full_tools_list(mcp_client)
                agent = create_strands_agent(
                    model="us.amazon.nova-premier-v1:0",
                    personality="nfl_analyst",
                    tools=tools,
                )
                
                # Execute the query
                agent(user_input)
                return True  # Success
                
        except Exception as e:
            if "Response ended prematurely" in str(e) and attempt < max_retries:
                print(f"Connection lost (attempt {attempt + 1}/{max_retries + 1}). Retrying in 2 seconds...")
                time.sleep(2)
                continue
            else:
                print(f"Error: {e}")
                return False
    
    return False

def run_agent(mcp_url: str, access_token: str):
    # Test connection first
    try:
        mcp_client = MCPClient(lambda: create_streamable_http_transport(mcp_url, access_token))
        with mcp_client:
            tools = get_full_tools_list(mcp_client)
            print(f"Found the following NFL MCP tools: {[tool.tool_name for tool in tools]}")
    except Exception as e:
        print(f"Failed to connect to MCP gateway: {e}")
        return
        
    print("\n🏈 NFL Data Analyst Ready!")
    print("I can help you with NFL statistics, game analysis, and player data.")
    print("Try asking: 'How many games were played in 2024?' or 'Search for playoff rules'")
    
    while True:
        user_input = input("\nAsk me something about NFL data (or 'exit' to quit): ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        print("\nThinking...\n")
        success = run_agent_with_retry(mcp_url, access_token, user_input)
        if not success:
            print("Sorry, I encountered an error processing your request. Please try again.")

if __name__ == "__main__":
    run_agent(gateway_url, fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL))
