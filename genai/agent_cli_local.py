from agent_config import create_strands_agent

def run_local_agent():
    """Run NFL agent with local tools (nfl_game_recap personality)"""
    
    print("🏈 NFL Game Recap Specialist Ready!")
    print("I can help you with NFL game analysis, schedules, and player data using local tools.")
    print("Try asking: 'Show me Cowboys games from 2024' or 'Get context for Patriots vs Bills'")
    
    # Create agent with local tools
    agent = create_strands_agent(
        model="us.amazon.nova-premier-v1:0",
        personality="nfl_game_recap",  # Uses local tools + knowledge base
    )
    
    while True:
        user_input = input("\nAsk me something about NFL games (or 'exit' to quit): ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        print("\nThinking...\n")
        try:
            agent(user_input)
        except Exception as e:
            print(f"Error: {e}")
            print("Please try a different question.")

if __name__ == "__main__":
    run_local_agent()
