# __init__.py

from .get_schedules import get_schedules
from .get_context import get_context
from .get_game_inputs import get_game_inputs
from .get_game_outputs import get_game_outputs
from .nfl_kb_search import nfl_kb_search

# List of all available tools
TOOLS = [
    get_schedules,
    get_context,
    get_game_inputs,
    get_game_outputs,
    nfl_kb_search
]

__all__ = [
    'get_schedules',
    'get_context', 
    'get_game_inputs',
    'get_game_outputs',
    'nfl_kb_search',
    'TOOLS'
]
