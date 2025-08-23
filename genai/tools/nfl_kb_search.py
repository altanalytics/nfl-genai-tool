# nfl_kb_search.py

from strands_tools.retrieve import retrieve
from typing import Optional

def nfl_kb_search(
    text: str,
    numberOfResults: Optional[int] = 5,
    score: Optional[float] = 0.4
) -> str:
    """
    Search the NFL knowledge base for statistical information, historical data, and analysis.

    This tool provides access to comprehensive NFL data, enabling queries about:
    - Player statistics and performance metrics
    - Team records and historical data
    - Game results and play-by-play analysis
    - Season trends and comparative analysis
    - Draft information and player profiles

    Results are sorted by relevance score and include source metadata.
    
    Args:
        text: The query to search for in the NFL knowledge base
        numberOfResults: The maximum number of results to return. Default is 5.
        score: Minimum relevance score threshold (0.0-1.0). Results below this score will be filtered out. Default is 0.4.
        
    Returns:
        str: Formatted search results from the NFL knowledge base
    """
    # Create a tool object in the format expected by the retrieve function
    tool = {
        "toolUseId": "nfl_kb_search",
        "input": {
            "text": text,
            "numberOfResults": numberOfResults,
            "score": score,
            "knowledgeBaseId": "RRKMVWLTTG",
            "region": "us-east-1"
        }
    }
    
    # Call the original retrieve function with our pre-configured settings
    result = retrieve(tool)
    
    # Extract the text content from the structured response
    if isinstance(result, dict) and "content" in result:
        content_list = result["content"]
        if content_list and isinstance(content_list, list) and len(content_list) > 0:
            return content_list[0].get("text", "No text content found")
    
    return str(result)
