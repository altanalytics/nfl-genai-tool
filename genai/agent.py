import os
from bedrock_agentcore import BedrockAgentCoreApp
from agent_config import create_strands_agent

app = BedrockAgentCoreApp()

@app.entrypoint
async def agent_invocation(payload):
    user_message = payload.get("prompt", "No prompt found in input...")
    model_selected = payload.get("model", "us.amazon.nova-micro-v1:0")
    model_persona = payload.get("personality", "basic")
    session_id = payload.get("session_id", "default-session")
    s3_session_bucket = payload.get("s3sessionbucket", "")
    
    print(f'Request - Model: {model_selected}, Personality: {model_persona}, Session: {session_id}, S3 Bucket: {s3_session_bucket}')
    
    # Split session ID on hyphen to get username and session
    if '-' in session_id:
        username, actual_session_id = session_id.split('-', 1)  # Split only on first hyphen
        s3_prefix = f"{username}/"
        print(f'Split session - Username: {username}, Session ID: {actual_session_id}, S3 Prefix: {s3_prefix}')
    else:
        # Fallback if no hyphen found
        actual_session_id = session_id
        s3_prefix = "default/"
        print(f'No hyphen in session ID, using default prefix: {s3_prefix}')
    
    # Create agent with S3 session management
    agent = create_strands_agent(
        model=model_selected, 
        personality=model_persona,
        session_id=actual_session_id,
        s3_bucket=s3_session_bucket,
        s3_prefix=s3_prefix
    )
    
    # tell UI to reset
    yield {"type": "start"}

    try:
        async for event in agent.stream_async(user_message):
            txt = event.get("data")
            if isinstance(txt, str) and txt:
                # UI will JSON.parse(e.data) and route by type
                yield {"type": "token", "text": txt}
    except Exception as e:
        # optional: surface errors to UI
        yield {"type": "error", "message": str(e)}

    # done marker for UI to stop spinners, etc.
    yield {"type": "done"}

if __name__ == "__main__":
    app.run()
