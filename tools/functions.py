from typing import List
from decimal import Decimal
from tools.modules import *
from config import *

from tools.helper.season_ratings import obtain_multiple_player_ratings
from tools.helper.season_stats import obtain_multiple_player_season_stats
from tools.helper.event_stats import get_player_property, obtain_player_event_stats
from tools.helper.event_summary import get_tournament_property, get_team_property, create_url_params, create_event_data


def obtain_event_performance_data(
        parameters : List[PlayerEventParameters]
) -> List[PlayerEventStats] | List[dict]:
    """
    Retrieve event-level statistics for multiple football players across specified parameters.

    Args:
        player_stats_parameters (dict): A dictionary that contains player names and event parameters. For each key-value pair,
            - The key is the player name (str)
            - The value is another dictionary where event parameters are specified. These parameters are;
                - event_date (str | Tuple[str,str] | List[str])
                - opponent_name (str)
                - tournament_name (str)

            - e.g. {
                "Dries Mertens": {"event_date": ("2024-11-16", "2024-12-16")},
                "Gabriel Sara": {"tournament_name": "UEFA Europa League", "opponent_name": "Tottenham Hotspur"}
            }
            
    Returns:
        List[PlayerEventStats] | List[dict]: A list of `PlayerEventStats` objects with detailed statistics or error dictionaries for bad inputs
    """
    all_player_stats = []
    error_messages = []
    
    player_id_cache = {}

    for params in parameters:
        player_name = params.player_name
        tournament_name = params.tournament_name
        event_date = params.event_date
        last_k = params.last_k
        opponent_team_name = params.opponent_team_name
        player_team_name = params.player_team_name
        
        player_id = player_id_cache.get(player_name)
        if player_id is None:
            player_id = get_player_property(player_name=player_name, col_name="PLAYER_ID")
            player_id_cache[player_name] = player_id
        
        if isinstance(player_id,list):
            error_messages.append({"error": {"message": "404", "parameter": "player_name", "value": player_name}})
        elif player_id is None:
            error_messages.append({"error": {"message": "405", "parameter": "player_name", "value": player_name}}) # Duplication
        elif isinstance(player_id, Decimal):
            player_id = int(player_id)

        all_player_stats.extend(
            obtain_player_event_stats(
                player_name = player_name,
                event_date = event_date,
                last_k = last_k,
                opponent_team_name = opponent_team_name,
                player_team_name = player_team_name,
                tournament_name = tournament_name,
                player_id = player_id
            )
        )

    if error_messages:
        return error_messages
    
    #if len(all_player_stats):
    
    return all_player_stats


def obtain_season_performance_data(
        parameters: List[PlayerSeasonParameters], 
        endpoint: Literal["stats", "ratings", "both"]
    ) -> List[PlayerSeasonStats] | List[dict] | List[PlayerSeasonRatings] | Union[List[PlayerSeasonStats] , List[PlayerSeasonRatings]]:
    """
    Fetch season level data for players.
    Queries DynamoDB, retrieves data from external APIs, and returns processed results.

    Args:
        parameters (List[SeasonParameters]): A list of player and tournament parameters. 
            If the user's question does not mention any of the following fields:
            - 'tournament_name', 'season_year', or 'tournament_country', 
              the value defaults to 'None'.
            - 'player_name' is always required.
              
        endpoint (Literal["stats", "ratings", "both"]): Specify the type of data to fetch. Defaults to "both".

    Example:
        user query: Summarize Cole Palmer performance in Premier League.
        function parameters:
            obtain_season_performance_data(
                parameters: {
                    "player_name": "Cole Palmer",
                    "tournament_name": "Premier League",
                    "tournament_country": "England",
                    "season_year": None
                }, 
                endpoint: "both"
            )
    """
    if endpoint=="both":
        stats = obtain_multiple_player_season_stats(player_stats_parameters=parameters)
        ratings = obtain_multiple_player_ratings(player_ratings_parameters=parameters)
        data = stats + ratings
        return data
    elif endpoint=="stats":
        stats = obtain_multiple_player_season_stats(player_stats_parameters=parameters)
        return stats
    elif endpoint=="ratings":
        ratings = obtain_multiple_player_ratings(player_ratings_parameters=parameters)
        return ratings


def obtain_summary_of_event(
    parameters : List[EventParameters]
) -> List[EventSummary]:
    event_summaries = []
    for params in parameters:
        event_date = params.event_date
        last_k = params.last_k
        home_team_name = params.home_team_name
        away_team_name = params.away_team_name
        tournament_name = params.tournament_name

        if tournament_name:
            tournament_id = get_tournament_property(query_value=tournament_name, col_name="TOURNAMENT_ID", gsi=True, key_name="TOURNAMENT_NAME")
        else: 
            tournament_id = None

        if home_team_name:
            home_team_id = get_team_property(team_name=home_team_name, col_name="TEAM_ID")
        else:
            home_team_id = None

        if away_team_name:
            away_team_id = get_team_property(team_name=away_team_name, col_name="TEAM_ID")
        else:
            away_team_id = None

        url_params = create_url_params(
            event_date=event_date,
            last_k=last_k,
            home_team_name=home_team_name,
            away_team_name=away_team_name,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            tournament_name=tournament_name,
            tournament_id=tournament_id,
            table_name="dim_events"
        )

        if not url_params:
            logger.info("Event with defined criteria is not found.")
            continue

        summary = True if len(url_params) > 4 else False

        event_datas = []
        for param in url_params:
            event_data = create_event_data(param=param, summary=summary)
            event_datas.append(event_data)

        event_summaries.append(event_datas)

    return event_summaries
    

