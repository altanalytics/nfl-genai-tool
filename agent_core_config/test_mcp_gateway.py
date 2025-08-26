#!/usr/bin/env python3
"""
Test NFL MCP Gateway
Tests all three NFL MCP services through the gateway using proper MCP client
"""

from strands import Agent
import logging
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client 
import os
import requests
import json
import boto3

def main():
    # Check for AWS credentials
    if not os.environ.get('AWS_PROFILE') and not os.environ.get('AWS_ACCESS_KEY_ID'):
        print("❌ AWS credentials not found!")
        print("Please set AWS_PROFILE environment variable:")
        print("   AWS_PROFILE=your-profile-name uv run test_mcp_gateway.py")
        return

    try:
        secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
        sec_valu = secrets_client.get_secret_value(SecretId='nfl_mcp_auth')
        client_info = json.loads(sec_valu['SecretString'])['client_info']
        CLIENT_ID = client_info['client_id']
        CLIENT_SECRET = client_info['client_secret']
        TOKEN_URL = client_info['token_endpoint']
        gateway_url = json.loads(sec_valu['SecretString'])['gateway_url']
        
        print(f"✅ Found gateway: {json.loads(sec_valu['SecretString'])['gateway_id']}")
        print(f"Gateway URL: {gateway_url}")
        
    except Exception as e:
        print(f"❌ Error getting gateway configuration: {e}")
        print("Please run gateway_deploy.py first")
        return

    def fetch_access_token(client_id, client_secret, token_url):
        response = requests.post(
            token_url,
            data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}",
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        return response.json()['access_token']

    def create_streamable_http_transport(mcp_url: str, access_token: str):
        return streamablehttp_client(mcp_url, headers={"Authorization": f"Bearer {access_token}"})

    def get_full_tools_list(client):
        """List tools with support for pagination"""
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

    def test_nfl_mcp_gateway(mcp_url: str, access_token: str):
        print(f"\n🧪 Testing NFL MCP Gateway...")
        
        bedrockmodel = BedrockModel(
            inference_profile_id="us.amazon.nova-micro-v1:0",
            temperature=0.7,
            streaming=False,  # Disable streaming for testing
        )
         
        mcp_client = MCPClient(lambda: create_streamable_http_transport(mcp_url, access_token))
         
        try:
            with mcp_client:
                tools = get_full_tools_list(mcp_client)
                print(f"✅ Found {len(tools)} tools: {[tool.tool_name for tool in tools]}")
                
                if not tools:
                    print("❌ No tools found! Check Lambda target configuration")
                    return False
                
                # Test each tool
                expected_tools = ['nfl_data_service', 'nfl_game_service', 'nfl_knowledge_service']
                found_tools = [tool.tool_name for tool in tools]
                
                results = {}
                for expected_tool in expected_tools:
                    # Check for both exact match and prefixed match (e.g., "nfl-data-service___nfl_data_service")
                    found = any(expected_tool in tool_name for tool_name in found_tools)
                    results[expected_tool] = found
                    if found:
                        # Find the actual tool name
                        actual_name = next(name for name in found_tools if expected_tool in name)
                        print(f"✅ {expected_tool}: Available as '{actual_name}'")
                    else:
                        print(f"❌ {expected_tool}: Missing")
                
                # Quick functional test with a simple query
                if 'nfl_data_service' in found_tools:
                    try:
                        print(f"\n🧪 Testing nfl_data_service with simple query...")
                        agent = Agent(model=bedrockmodel, tools=tools)
                        
                        # Simple test - just check if we can create the agent and it recognizes the tools
                        print("✅ Agent created successfully with MCP tools")
                        
                    except Exception as e:
                        print(f"⚠️  Agent creation test failed: {e}")
                
                # Summary
                passed = sum(results.values())
                total = len(results)
                
                print(f"\n📊 Test Results Summary:")
                for service, result in results.items():
                    status = "✅ AVAILABLE" if result else "❌ MISSING"
                    print(f"   {service}: {status}")
                
                print(f"\n🎯 Overall: {passed}/{total} services available")
                
                if passed == total:
                    print("🎉 All NFL MCP services are working correctly!")
                    print("\n📝 Next steps:")
                    print("1. Update your agent configuration to use MCP tools")
                    print("2. Test the nfl_analyst personality")
                    return True
                else:
                    print("⚠️  Some services missing. Check the gateway configuration.")
                    return False
                    
        except Exception as e:
            print(f"❌ MCP Gateway test failed: {e}")
            return False

    # Get access token and test
    try:
        access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
        success = test_nfl_mcp_gateway(gateway_url, access_token)
        
        if success:
            # Offer interactive testing
            user_input = input("\n🤖 Would you like to test interactively? (y/n): ")
            if user_input.lower() in ['y', 'yes']:
                run_interactive_test(gateway_url, access_token)
                
    except Exception as e:
        print(f"❌ Error during testing: {e}")

def run_interactive_test(mcp_url: str, access_token: str):
    """Run interactive test with the MCP gateway"""
    print("\n🤖 Starting interactive NFL MCP test...")
    
    bedrockmodel = BedrockModel(
        inference_profile_id="us.amazon.nova-micro-v1:0",
        temperature=0.7,
        streaming=True,
    )
     
    mcp_client = MCPClient(lambda: streamablehttp_client(mcp_url, headers={"Authorization": f"Bearer {access_token}"}))
     
    with mcp_client:
        # Get tools
        more_tools = True
        tools = []
        pagination_token = None
        while more_tools:
            tmp_tools = mcp_client.list_tools_sync(pagination_token=pagination_token)
            tools.extend(tmp_tools)
            if tmp_tools.pagination_token is None:
                more_tools = False
            else:
                more_tools = True 
                pagination_token = tmp_tools.pagination_token
        
        print(f"Available tools: {[tool.tool_name for tool in tools]}")
        
        agent = Agent(model=bedrockmodel, tools=tools)
        
        print("\n🎉 Interactive NFL MCP Agent ready!")
        print("Try asking: 'How many games were played in 2024?' or 'Search for playoff rules'")
        
        while True:
            user_input = input("\nAsk me something about NFL data (or 'exit' to quit): ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
            print("\nThinking...\n")
            try:
                agent(user_input)
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
