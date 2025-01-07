from tools.functions import obtain_season_performance_data, obtain_event_performance_data, obtain_summary_of_event
from pydantic import BaseModel
from typing import Dict, Literal, List, Optional
from langchain.tools import StructuredTool
from tools.modules import *
from langchain_community.tools.tavily_search import TavilySearchResults


SEASON_PERFORMANCE_TOOL = StructuredTool.from_function(
    func=obtain_season_performance_data,
    name="obtain_season_performance_data",
    description="""
        Fetch season level data for players. 
        This tool should be used when asked about a player's performance in a full season or a tournament. 
        endpoint argument defaults to 'both' unless askes for stats or ratings specifically
        If the user's question does not mention one of the following fields—'tournament_name', 'season_year', or 'tournament_country'—their values default to 'None'. 
        'player_name' is always required.
    """,
    args_schema=PlayerSeasonPerformanceArgs,  # Explicit schema
    infer_schema=True  # Ensure schema inference is disabled
)

EVENT_PERFORMANCE_TOOL = StructuredTool.from_function(
    func=obtain_event_performance_data,
    name="obtain_event_performance_data",
    description="Fetch event level data for players. This tool should be used when asked about a player's performance in a specific football match / set of matches",
    args_schema=PlayerEventPerformanceArgs,  # Explicit schema
    infer_schema=False  # Ensure schema inference is disabled
)

EVENT_SUMMARY_TOOL = StructuredTool.from_function(
    func=obtain_summary_of_event,
    name="obtain_summary_of_event",
    description="""
    Fetches the summary of a football match. 
    This tool should be used when human message asks about a football match in general without asking about any specific players.
    The data it returns contains list of important incidents (goals, cards, penalties) about the match, and the squads of both sides.
    """,
    args_schema=EventSummaryArgs,
    infer_schema=False
)
