import boto3

session = boto3.Session()
client = session.client('bedrock-agentcore-control', region_name="us-east-1")

# Get Account ID
sts_client = session.client("sts")
identity = sts_client.get_caller_identity()
account_id = identity["Account"]

# Get existing agent runtime
response = client.list_agent_runtimes()
agent_runtime_id = None

for runtime in response['agentRuntimes']:
    if runtime['agentRuntimeName'] == 'strands_agent':
        agent_runtime_id = runtime['agentRuntimeId']
        break

if not agent_runtime_id:
    print("❌ No agent runtime found with name 'strands_agent'")
    print("Please run agent_deploy.py first")
    exit(1)

print(f"🔄 Updating Agent Runtime ID: {agent_runtime_id}")
print(f"📋 Agent Runtime ARN: arn:aws:bedrock-agentcore:us-east-1:{account_id}:runtime/{agent_runtime_id}")
print(f"🏢 Account ID: {account_id}")

# Update the agent runtime
print("🚀 Updating agent runtime...")
response = client.update_agent_runtime(
    agentRuntimeId=agent_runtime_id,
    agentRuntimeArtifact={
        'containerConfiguration': {
            'containerUri': f"{account_id}.dkr.ecr.us-east-1.amazonaws.com/my-strands-agent:latest"
        }
    },
    roleArn=f'arn:aws:iam::{account_id}:role/bedrock-agent-core-role',
    networkConfiguration={"networkMode": "PUBLIC"}
)

print(f"✅ Agent Runtime updated successfully!")
print(f"📋 Agent Runtime ARN: {response['agentRuntimeArn']}")
print(f"📊 Status: {response['status']}")
print(f"🕐 Last Modified: {response.get('lastModifiedTime', 'N/A')}")
print(f"⏳ Agent runtime is updating. This may take a few minutes.")
print(f"💡 You can check the status using the AWS console or describe_agent_runtime API.")
print(f"📝 Note: CloudWatch logging is configured at the role level")
