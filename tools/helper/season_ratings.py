from langchain_core.tools import tool
from typing import Dict, List, Union, Optional, TypedDict, Literal, Any
import requests
import numpy as np
from boto3.dynamodb.conditions import Key, Attr
from config import *
from tools.modules import *
import boto3
from decimal import Decimal
import time

from dataclasses import dataclass


def get_big_club_ids(input_team_id: int, table_name: str):
    """
    Finds other teams with at least 80% of the market value of the input team from DynamoDB using a GSI.
    
    Args:
        input_team_id (int): The ID of the input team.
        table_name (str): The name of the DynamoDB table containing the teams data.
        gsi_name (str): The name of the Global Secondary Index (GSI) on TOTAL_MARKET_VALUE.
        
    Returns:
        list: List of team IDs with at least 80% of the market value of the input team.
    """
    
    # Reference the DynamoDB table
    try:
        # Query DynamoDB for the input team to get its market value
        response = requests.post(
            url=QUERY_LAMBDA_URL,
            json = {
                "table_name": "dim_teams",
                "index_name": 'TEAM_ID',
                "operation": "eq",
                "query_value": input_team_id
            }
        ).json()

        # Check if the team exists
        if 'Items' not in response or len(response['Items']) == 0:
            raise ValueError(f"Team ID {input_team_id} not found in the database.")
        
        input_team_row = response['Items'][0]
        input_market_value = Decimal(input_team_row['TOTAL_MARKET_VALUE'])

        # Calculate the threshold market value (80% of the input team's market value)
        threshold = int(0.8 * float(input_market_value))

        # Retrieve all teams with market value >= threshold using the GSI
        scan_payload = {
            "table_name": table_name,
            "index_name": "TOTAL_MARKET_VALUE",
            "filter": {
                "type": "logical",
                "operation": "and",
                "subfilters": [
                    {
                        "type": "atomic",
                        "attribute": "TOTAL_MARKET_VALUE",
                        "operation": "gte",
                        "value": threshold
                    },
                    {
                        "type": "atomic",
                        "attribute": "TEAM_ID",
                        "operation": "ne",
                        "value": input_team_id
                    }
                ]
            }
        }
        
        scan_response = requests.post(SCAN_LAMBDA_URL, json=scan_payload)
        scan_response.raise_for_status()  # Raise an error for HTTP codes >= 400
        scan_results = scan_response.json()

        # Extract team IDs from the scan results
        similar_teams = [int(item['TEAM_ID']) for item in scan_results]
        return similar_teams

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request Error: {e}")
        return []
    except Exception as e:
        print(f"Error retrieving big clubs: {e}")
        return []

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

# client

def create_url_params(player_id: int, tournament_name: str | None, tournament_country: str | None, season_year: int | None, table_name:str) -> List[dict]:
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


def process_player_ratings(data: dict, big_club_ids: List[int]) -> ProcessedRating:
    """
    Analyze player performance based on given JSON data and big club IDs.

    Args:
        data (dict): JSON data containing season ratings and events.
        big_club_ids (list): List of integers representing big club IDs.

    Returns:
        dict: A dictionary with games count, average rating, rating std deviation,
              and average rating against big clubs.
    """
    season_ratings = data.get("seasonRatings", [])
    
    # Initialize lists for ratings and big club ratings
    all_ratings = []
    big_game_ratings = []
    big_game_count = 0

    for rating_data in season_ratings:
        # Extract relevant data
        rating = rating_data.get("rating")
        is_home = rating_data.get("isHome")
        home_team = rating_data["event"]["homeTeam"]["id"]
        away_team = rating_data["event"]["awayTeam"]["id"]
        
        # Determine opponent team ID
        own_team_id = home_team if is_home else away_team
        opponent_team_id = away_team if is_home else home_team
        
        # Add the rating to the overall list
        if rating is not None:
            all_ratings.append(rating)
            
            # If the opponent is a big club, add the rating to the big club list
            # TODO: Implement more scenarios to big game selection. e.g. All games in UCL
            if opponent_team_id in big_club_ids:
                big_game_ratings.append(rating)
                big_game_count += 1
    
    # Calculate statistics
    games_count = len(all_ratings)
    average_rating = np.mean(all_ratings) if all_ratings else None
    rating_std_dev = np.std(all_ratings) if all_ratings else None
    average_big_game_rating = np.mean(big_game_ratings) if big_game_ratings else None
    
    # Return the results as a dictionary
    return {
        "game_count": games_count,
        "big_game_count": big_game_count,
        "average_rating": average_rating,
        "rating_std_dev": rating_std_dev,
        "average_big_game_rating": average_big_game_rating,
    }

def request_player_season_ratings(player_id, tournament_id, unique_season_id):
    url = f"https://www.sofascore.com/api/v1/player/{player_id}/unique-tournament/{tournament_id}/season/{unique_season_id}/ratings"
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

def retrieve_player_season_ratings(player_name: str, param: dict, big_club_ids: List[int]) -> PlayerSeasonRatings:
    player_id, tournament_id, unique_season_id, tournament_name, season_year = param.get("PLAYER_ID"), param.get("TOURNAMENT_ID"), param.get("UNIQUE_SEASON_ID"), param.get("TOURNAMENT_NAME"), param.get("SEASON_YEAR")

    if None in [player_id, tournament_id, unique_season_id]:
        raise ValueError("One of the ratings url parameters is None.")

    ratings = request_player_season_ratings(player_id, tournament_id, unique_season_id)

    if ratings.get("error"):
        if ratings.get("error").get("code") == 404:
            error_info = "Player did not play in this tournament for this particular season"
            return None
        else:
            raise ValueError(f"URL request failed with code {ratings.get('error').get('code')} and message {ratings.get('error').get('message')}")
    else:
        ratings_processed = process_player_ratings(data=ratings, big_club_ids=big_club_ids)

    return PlayerSeasonRatings(
        player_id=int(player_id),
        player_name=player_name,
        tournament_name=tournament_name,
        tournament_id=int(tournament_id),
        unique_season_id=int(unique_season_id),
        season_year=int(season_year),
        average_rating=ratings_processed["average_rating"],
        average_big_game_rating=ratings_processed["average_big_game_rating"],
        game_count=ratings_processed["game_count"],
        big_game_count=ratings_processed["big_game_count"],
        rating_std_dev=ratings_processed["rating_std_dev"]
    )

def obtain_player_ratings(
        player_name: str, 
        tournament_name: str | None, 
        tournament_country: str | None, 
        season_year: int | None, 
        big_club_ids: List[int], 
        player_id: Optional[int] = None) -> List[PlayerSeasonRatings] | dict:
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
    
    player_ratings = []
    for param in url_params:
        player_season_ratings = retrieve_player_season_ratings(player_name=player_name, param=param, big_club_ids=big_club_ids)
        if player_season_ratings:
            player_ratings.append(player_season_ratings)

    return player_ratings

def obtain_multiple_player_ratings(player_ratings_parameters: List[PlayerSeasonParameters]) -> List[PlayerSeasonRatings] | List[dict]:
    """
    Fetch season level ratings for multiple players. The tool queries DynamoDB for parameters, retrieves stats from external APIs, and returns processed results.

    Args:
        player_ratings_parameters (dict): A dictionary that contains player names and event parameters. For each key-value pair,
            - The key is the player name (str)
            - The value is another dictionary where event parameters are specified. These parameters are;
                - season_year (int)
                - tournament_name (str)
                - tournament_country (str)
                
    Returns:
        List[PlayerRatings] | List[dict]: A list of `PlayerRatings` objects with event ratings of the player or error dictionaries for bad inputs

    Example:
        Input:
        {
            "Dries Mertens": {"tournament_name": "Trendyol Süper Lig", "season_year": None},
            "Mauro Icardi": {"tournament_name": None, "season_year": 2023}
        }
    """
    all_player_ratings = []
    error_messages = []
    player_id_cache = {}

    for params in player_ratings_parameters:
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
        
        team_id = get_player_property(player_name=player_name, col_name="TEAM_ID")
        
        #team_data = pd.read_csv(r"C:\Users\herdogan\Documents\GitHub\langgraph-test\team_data.csv")
        #big_club_ids = get_big_club_ids(df=team_data, input_team_id=team_id)
        
        big_club_ids = get_big_club_ids(input_team_id=team_id, table_name="dim_teams")
        
        all_player_ratings.extend(
            obtain_player_ratings(
                player_name=player_name,
                tournament_name=tournament_name,
                season_year=season_year,
                tournament_country=tournament_country,
                player_id=player_id,
                big_club_ids=big_club_ids
            )
        )
    if error_messages:
        return error_messages
    
    return all_player_ratings