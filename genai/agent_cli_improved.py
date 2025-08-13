#!/usr/bin/env python3
import asyncio
import re
from agent_config import create_strands_agent

GREEN = "\033[92m"; RESET = "\033[0m"
OPEN = re.compile(r"<\s*thinking\s*>", re.I)
CLOSE = re.compile(r"<\s*/\s*thinking\s*>", re.I)

def colorize_thinking(s: str) -> str:
    return CLOSE.sub(RESET, OPEN.sub(GREEN, s)) + RESET

async def main():
    agent = create_strands_agent()
    print("🤖 Strands CLI Chatbot - Type 'quit' to exit\n" + "-"*50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in {"quit", "exit", "q"}: 
                print("Goodbye! 👋")
                break
            if not user_input: 
                continue
                
            print("\nBot: ", end="", flush=True)
            
            # Use stream_async for better tool handling
            full_response = ""
            async for event in agent.stream_async(user_input):
                # Handle different event types properly
                if isinstance(event, dict):
                    # Handle structured events (like from bedrock-agent-core)
                    if "data" in event:
                        chunk = event["data"]
                        if isinstance(chunk, str) and chunk:
                            print(chunk, end="", flush=True)
                            full_response += chunk
                elif isinstance(event, str):
                    # Handle direct string events
                    print(event, end="", flush=True)
                    full_response += event
                else:
                    # Handle other event types (like response objects)
                    text_content = str(event)
                    if text_content and text_content not in full_response:
                        print(colorize_thinking(text_content), end="", flush=True)
                        full_response += text_content
            
            print()  # New line after response
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Try restarting the conversation or using a different input.")

if __name__ == "__main__":
    asyncio.run(main())
