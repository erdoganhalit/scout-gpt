from langchain_core.tools import tool
from typing import Dict, List, Union, Optional, Literal, Any
import requests
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from config import *
import boto3
from dataclasses import dataclass
from tools.modules import *
import time

def request_player_seasons(player_id: int) -> dict:
    url = f"https://www.sofascore.com/api/v1/player/{str(player_id)}/statistics/seasons"
    if USE_PROXIES:
        for i, proxy in enumerate(PROXIES):
            try:
                start_time = time.time()  # Start the timer
                response = requests.get(url, proxies={"http": proxy}, timeout=10)
                response_time = time.time() - start_time  # Calculate response time
                if response.status_code == 200:
                    print(f"Success with proxy number {i+1} : {proxy} in {response_time:.2f} seconds")
                    return response.json()
            except Exception as e:
                time.sleep(2)  # Add delay to avoid bans
        raise Exception("All proxies failed!")
    else:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()

def get_player_property(player_name: str, col_name: str) -> int | List[int] | None:
    """
    Tool to get the unique id or other property of a football player from DynamoDB.
    
    Args:
        player_name (str): The name of the football player.
        col_name (str): The column name for the property you want to retrieve.

    Returns:
        The value of the specified column for the player whose name is given.
    """

    # Assuming the 'dim_players' table has a partition key 'PLAYER_NAME'

    try:
        # Query DynamoDB for the player name
        response = requests.post(
            url=QUERY_LAMBDA_URL,
            json = {
                "table_name": "dim_players",
                "gsi": "true",
                "index_name": 'PLAYER_NAME',
                "operation": "eq",
                "query_value": player_name
            }
        ).json()
        
        # Check if player data exists
        if 'Items' in response and len(response['Items']) > 0:
            if len(response["Items"]) == 1:
                player_item = response['Items'][0]  # Take the first result if there are multiple matches
                
                # Return the value of the requested column
                if col_name in player_item:
                    return player_item[col_name]
                else:
                    raise ValueError(f"Column '{col_name}' not found in player data.")
            elif len(response["Items"]) > 1:
                ids = []
                for player_item in response["Items"]:
                    if col_name in player_item:
                        ids.append(player_item[col_name])
                    else:
                        raise ValueError(f"Column '{col_name}' not found in player data.")
                return ids
        else:
            print(f"Player '{player_name}' not found in the database.")
            return None

    except Exception as e:
        print(f"Error retrieving data for player '{player_name}': {e}")

def create_url_params(player_id: int, tournament_name: str | None, tournament_country: str | None, season_year: int | None, table_name: str) -> List[dict]:
    """
    Tool to get the unique ids of tournaments and optionally a specific season.
    
    Args:
        player_id (int): The ID of the player.
        tournament_name (str | None): The name of the tournament (optional).
        season_year (int | None): The year of the season (optional).
        
    Returns:
        List[dict]: A list of dictionaries with the necessary parameters.
    """

    # Reference the DynamoDB table dim_unique_seasons

    if tournament_country and tournament_name:
        tournament_query_field = "TOURNAMENT_FULL_NAME"
        tournament_query_key = tournament_country + "-" + tournament_name
    else:
        tournament_query_field = "TOURNAMENT_NAME"
        tournament_query_key = tournament_name

    if tournament_name is None:
        if season_year is None:
            # When both tournament_name and season_year are None
            raise ValueError("At least one of tournament_name or season_year must be provided.")
        else:
            # When only season_year is specified, query by season year
            url_params = []
            response = request_player_seasons(player_id=player_id)  # Assuming this fetches necessary data
            for item in response["uniqueTournamentSeasons"]:
                tournament_id = item["uniqueTournament"]["id"]
                for season in item["seasons"]:
                    if season["year"] in [str(season_year), str(season_year)[-2:] + "/" + str(season_year+1)[-2:]]:
                        url_params.append(
                            {
                                "PLAYER_ID": player_id,
                                "TOURNAMENT_ID": tournament_id,
                                "UNIQUE_SEASON_ID": season["id"],
                                "TOURNAMENT_NAME": item["uniqueTournament"]["name"],
                                "SEASON_YEAR": season_year
                            }
                        )
                
    else:
        if season_year is None:
            # When only tournament_name is specified
            url_params = []
            # Query DynamoDB for the tournament name
            response = requests.post(
                url=QUERY_LAMBDA_URL,
                json = {
                    "table_name": table_name,
                    "gsi": "true",
                    "index_name": tournament_query_field,
                    "operation": "eq",
                    "query_value": tournament_query_key
                }
            ).json()
            if 'Items' in response and len(response['Items']) > 0:
                for item in response['Items']:
                    item["PLAYER_ID"] = player_id
                    url_params.append(item)
            else:
                print(f"Tournament '{tournament_name}' not found.")
        else:
            # When both tournament_name and season_year are specified
            url_params = []
            response = requests.post(
                url=QUERY_LAMBDA_URL,
                json = {
                    "table_name": table_name,
                    "gsi": "true",
                    "index_name": tournament_query_field,
                    "operation": "eq",
                    "query_value": tournament_query_key
                }
            ).json()
            if 'Items' in response and len(response['Items']) > 0:
                for item in response['Items']:
                    # Assuming that "SEASON_YEAR" is part of the item and matches
                    if item["SEASON_YEAR"] == season_year:
                        item["PLAYER_ID"] = player_id
                        url_params.append(item)
            else:
                print(f"Tournament '{tournament_name}' not found.")

    return url_params

def request_player_season_stats(player_id, tournament_id, unique_season_id):
    url = f"https://www.sofascore.com/api/v1/player/{player_id}/unique-tournament/{tournament_id}/season/{unique_season_id}/statistics/overall"
    if USE_PROXIES:
        for i, proxy in enumerate(PROXIES):
            try:
                start_time = time.time()  # Start the timer
                response = requests.get(url, proxies={"http": proxy}, timeout=10)
                response_time = time.time() - start_time  # Calculate response time
                if response.status_code == 200:
                    print(f"Success with proxy number {i+1} : {proxy} in {response_time:.2f} seconds")
                    return response.json()
            except Exception as e:
                time.sleep(2)  # Add delay to avoid bans
        raise Exception("All proxies failed!")
    else:
        response = requests.get(url, timeout=10)
        return response.json()

def create_player_season_stats(player_name: str, param: dict) -> PlayerSeasonStats:
    player_id, tournament_id, unique_season_id, tournament_name, season_year = param.get("PLAYER_ID"), param.get("TOURNAMENT_ID"), param.get("UNIQUE_SEASON_ID"), param.get("TOURNAMENT_NAME"), param.get("SEASON_YEAR")

    if None in [player_id, tournament_id, unique_season_id]:
        raise ValueError("One of the stats url parameters is None.")

    stats = request_player_season_stats(player_id, tournament_id, unique_season_id)

    if stats.get("error"):
        if stats.get("error").get("code") == 404:
            #stats = {"info": "Player did not play in this tournament for this particular season"}
            return None
        else:
            raise ValueError(f"URL request failed with code {stats.get('error').get('code')} and message {stats.get('error').get('message')}")

    return PlayerSeasonStats(
        player_id=int(player_id),
        player_name=player_name,
        tournament_name=tournament_name,
        tournament_id=int(tournament_id),
        unique_season_id=int(unique_season_id),
        season_year=int(season_year),
        stats=stats.get("statistics")
    )

def obtain_player_stats(
        player_name: str, 
        tournament_name: str | None, 
        tournament_country: str | None, 
        season_year: int | None,
        player_id: Optional[int] = None
    ) -> List[PlayerSeasonStats] | dict:
    if player_id is None:
        player_id = get_player_property(player_name=player_name, col_name="PLAYER_ID")

        if isinstance(player_id,list):
            return {"error": {"message": "404", "parameter": "player_name", "value": player_name}}
        elif player_id is None:
            return {"error": {"message": "405", "parameter": "player_name", "value": player_name}} # Duplication
        elif isinstance(player_id, Decimal):
            player_id = int(player_id)
            
    url_params = create_url_params(
        player_id=player_id, 
        tournament_name=tournament_name,
        tournament_country=tournament_country, 
        season_year=season_year,
        table_name="dim_unique_seasons"
    )
    
    player_stats = []
    for param in url_params:
        player_season_stats = create_player_season_stats(player_name=player_name, param=param)
        if player_season_stats:
            player_stats.append(player_season_stats)

    return player_stats

def obtain_multiple_player_season_stats(player_stats_parameters: List[PlayerSeasonParameters]) -> List[PlayerSeasonStats] | List[dict]:
    """
    Fetch season level statistics for multiple players. The tool queries DynamoDB for parameters, retrieves stats from external APIs, and returns results.

    Args:
        player_stats_parameters (dict): A dictionary where keys are player names (str) and values are dictionaries 
                                         containing optional tournament and season information. 
                                         Each value dictionary can include:
                                         - "tournament_name" (str): (optional).
                                         - "tournament_country" (str): (optional).
                                         - "season_year" (int): (optional).

    Returns:
        List[PlayerStats] | List[dict]: A list of `PlayerStats` objects with detailed statistics or error dictionaries for bad inputs
        
    Example:
        Input:
        {
            "Lionel Messi": {"tournament_name": "La Liga", "season_year": 2021}
        }
    """
    all_player_stats = []
    error_messages = []
    player_id_cache = {}
    for params in player_stats_parameters:
        player_name = params.player_name
        tournament_name = params.tournament_name
        season_year = params.season_year
        tournament_country = params.tournament_country

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
            obtain_player_stats(
                player_name=player_name,
                tournament_name=tournament_name,
                tournament_country=tournament_country,
                season_year=season_year,
                player_id=player_id
            )
        )

    if error_messages:
        return error_messages
    
    return all_player_stats


###############################################################
# TOOL ARGUMENTS CLASS
###############################################################
