from langchain_core.tools import tool
from typing import Dict, List, Union, Optional, Literal, Tuple, Any
import requests
from decimal import Decimal
from config import *
from tools.modules import *
import time
from datetime import datetime
from dataclasses import dataclass


def get_player_property(player_name: str, col_name: str) -> int | List[int] | None:
    """
    Tool to get the unique id or other property of a football player from DynamoDB.
    
    Args:
        player_name (str): The name of the football player.
        col_name (str): The column name for the property you want to retrieve.

    Returns:
        The value of the specified column for the player whose name is given.
    """

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
            return False

    except Exception as e:
        print(f"Error retrieving data for player '{player_name}': {e}")

def get_team_property(team_name: str, col_name: str) -> int | List[int] | None:
    """
    Tool to get the unique id or other property of a football team from DynamoDB.
    
    Args:
        team_name (str): The name of the football team.
        col_name (str): The column name for the property you want to retrieve.

    Returns:
        The value of the specified column for the team whose name is given.
    """

    # Assuming the 'dim_teams' table has a partition key 'PLAYER_NAME'

    try:
        # Query DynamoDB for the team name
        response = requests.post(
            url=QUERY_LAMBDA_URL,
            json = {
                "table_name": "dim_teams",
                "gsi": "true",
                "index_name": 'TEAM_NAME',
                "operation": "eq",
                "query_value": team_name
            }
        ).json()
        
        # Check if team data exists
        if 'Items' in response and len(response['Items']) > 0:
            if len(response["Items"]) == 1:
                team_item = response['Items'][0]  # Take the first result if there are multiple matches
                
                # Return the value of the requested column
                if col_name in team_item:
                    return team_item[col_name]
                else:
                    raise ValueError(f"Column '{col_name}' not found in team data.")
            elif len(response["Items"]) > 1:
                ids = []
                for team_item in response["Items"]:
                    if col_name in team_item:
                        ids.append(team_item[col_name])
                    else:
                        raise ValueError(f"Column '{col_name}' not found in team data.")
                return ids
        else:
            print(f"Team '{team_name}' not found in the database.")
            return False

    except Exception as e:
        print(f"Error retrieving data for team '{team_name}': {e}")

def get_tournament_property(query_value: str, col_name: str, key_name: str, gsi: bool) -> int | List[int] | None:
    """
    Tool to get the unique id or other property of a football tournament from DynamoDB.
    
    Args:
        query_value (str): Value to be queried.
        col_name (str): The column name for the property you want to retrieve.

    Returns:
        The value of the specified column for the tournament whose name is given.
    """

    try:
        # Query DynamoDB for the tournament name
        if gsi:
            response = requests.post(
                url=QUERY_LAMBDA_URL,
                json = {
                    "table_name": "dim_tournaments",
                    "gsi": "true",
                    "index_name": key_name,
                    "operation": "eq",
                    "query_value": query_value
                }
            ).json()
        else:
            response = requests.post(
                url=QUERY_LAMBDA_URL,
                json = {
                    "table_name": "dim_tournaments",
                    "index_name": key_name,
                    "operation": "eq",
                    "query_value": query_value
                }
            ).json()
        
        # Check if tournament data exists
        if 'Items' in response and len(response['Items']) > 0:
            if len(response["Items"]) == 1:
                tournament_item = response['Items'][0]  # Take the first result if there are multiple matches
                
                # Return the value of the requested column
                if col_name in tournament_item:
                    return tournament_item[col_name]
                else:
                    raise ValueError(f"Column '{col_name}' not found in tournament data.")
            elif len(response["Items"]) > 1:
                ids = []
                for tournament_item in response["Items"]:
                    if col_name in tournament_item:
                        ids.append(tournament_item[col_name])
                    else:
                        raise ValueError(f"Column '{col_name}' not found in tournament data.")
                return ids
        else:
            print(f"Tournament '{query_value}' not found in the database.")
            return False

    except Exception as e:
        print(f"Error retrieving data for tournament '{query_value}': {e}")

def create_url_params(
        player_id: int,
        event_date: str | Tuple[str,str] | List[str] | None,
        last_k: int | None,
        player_team_id: int | None,
        opponent_team_id: int | None,
        tournament_id: int | None,
        player_team_name: str | None,
        opponent_team_name: str | None,
        tournament_name: str | None,
        table_name:str,
        ) -> List[dict]:
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
    payload = {
        "table_name": table_name,
        "filter": {
            "type": "logical",
            "operation": "and",
            "subfilters": []
        }
    }

    if not player_team_id:
        # TODO: Get team id from player_id
        raise ValueError("player_team_id is required for this query.")
    
    # Add team-related conditions (home vs. away logic)
    if opponent_team_id:
        payload['filter']['subfilters'].append(
            {
                "type": "logical",
                "operation": "or",
                "subfilters": [
                    {
                        "type": "logical",
                        "operation": "and",
                        "subfilters": [
                            {
                                "type": "atomic",
                                "attribute": "HOME_TEAM_ID",
                                "operation": "eq",
                                "value": player_team_id
                            },
                            {
                                "type": "atomic",
                                "attribute": "AWAY_TEAM_ID",
                                "operation": "eq",
                                "value": opponent_team_id
                            },
                        ]
                    },
                    {
                        "type": "logical",
                        "operation": "and",
                        "subfilters": [
                            {
                                "type": "atomic",
                                "attribute": "HOME_TEAM_ID",
                                "operation": "eq",
                                "value": opponent_team_id
                            },
                            {
                                "type": "atomic",
                                "attribute": "AWAY_TEAM_ID",
                                "operation": "eq",
                                "value": player_team_id
                            },
                        ]
                    }
                ]
            }
        )
    else:
        payload['filter']['subfilters'].append(
            {
                "type": "logical",
                "operation": "or",
                "subfilters": [
                    {
                        "type": "atomic",
                        "attribute": "HOME_TEAM_ID",
                        "operation": "eq",
                        "value": player_team_id
                    },
                    {
                        "type": "atomic",
                        "attribute": "AWAY_TEAM_ID",
                        "operation": "eq",
                        "value": player_team_id
                    },
                ]
            }
        )

    if event_date:
        if isinstance(event_date, str):
            payload['filter']['subfilters'].append(
                {
                    "type": "atomic",
                    "attribute": "EVENT_DATE",
                    "operation": "eq",
                    "value": event_date
                }
            )
        elif isinstance(event_date, tuple | list):
            if len(event_date) == 2:
                payload['filter']['subfilters'].append(
                    {
                        "type": "atomic",
                        "attribute": "EVENT_DATE",
                        "operation": "between",
                        "value": event_date
                    }
                )
            else:
                raise ValueError(f"Event date list or tuple should have exactly two values. One start date, one end date. This one has {len(event_date)} values. Player ID {player_id} , Player team name: {player_team_name}")
        else:
            raise ValueError(f"Event date type can be either str, tuple, or list. Retrieved an event_date object of type {type(event_date)}")   
    if tournament_id:
        payload['filter']['subfilters'].append(
            {
                "type": "atomic",
                "attribute": "TOURNAMENT_ID",
                "operation": "eq",
                "value": tournament_id
            }
        )

    # Execute the query
    try:
        response = requests.post(
            url=SCAN_LAMBDA_URL,
            json=payload
        ).json()
        events = response
    except Exception as e:
        print(f"Error querying DynamoDB: {e}")

    url_params = []

    if not events:
        return []
    
    if last_k:
        sorted_events = sorted(
            events,
            key=lambda x: datetime.strptime(x['EVENT_DATE'], '%Y-%m-%d'),  # Adjust date format if needed
            reverse=True
        )
        events = sorted_events[:last_k]

    for event in events:
        event["PLAYER_ID"] = player_id
        event["PLAYER_TEAM_ID"] = player_team_id    
        
        if tournament_name:
            event["TOURNAMENT_NAME"] = tournament_name
        else:
            event["TOURNAMENT_NAME"] = get_tournament_property(query_value=event.get("TOURNAMENT_ID"), col_name="TOURNAMENT_NAME", key_name="TOURNAMENT_ID", gsi=False)
        
        if player_team_name:
            event["PLAYER_TEAM_NAME"] = player_team_name
        else:
            event["PLAYER_TEAM_NAME"] = event["HOME_TEAM_NAME"] if event["HOME_TEAM_ID"]==player_team_id else event["AWAY_TEAM_NAME"]
        
        if opponent_team_name:
            event["OPPONENT_TEAM_NAME"] = opponent_team_name
        else:
            event["OPPONENT_TEAM_NAME"] = event["AWAY_TEAM_NAME"] if event["HOME_TEAM_ID"]==player_team_id else event["HOME_TEAM_NAME"]
        
        if event["HOME_TEAM_ID"]==player_team_id:
            event["IS_HOME"] = True
        else:
            event["IS_HOME"] = False
        
        url_params.append(event)

    return url_params

def request_player_event_stats(player_id, event_id):
    url = f"https://www.sofascore.com/api/v1/event/{event_id}/player/{player_id}/statistics"
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

def create_player_event_stats(player_name: str, param: dict) -> PlayerEventStats:

    player_id = param.get("PLAYER_ID")
    event_id = param.get("EVENT_ID")


    player_stats = PlayerEventStats(
        player_id=int(param.get("PLAYER_ID")),
        player_name=player_name,
        event_date=param.get("EVENT_DATE"),
        player_team_name=param.get("PLAYER_TEAM_NAME"),
        opponent_team_name=param.get("OPPONENT_TEAM_NAME"),
        tournament_name=param.get("TOURNAMENT_NAME"),
        is_home = param.get("IS_HOME")
    )

    player_stats.player_team_score, player_stats.opponent_team_score = (int(param.get("HOME_SCORE")), int(param.get("AWAY_SCORE"))) if player_stats.is_home else (int(param.get("AWAY_SCORE")), int(param.get("HOME_SCORE"))) 

    winner_code = int(param.get("WINNER_CODE"))
    if winner_code == 1 and player_stats.is_home==True:
        player_stats.match_result = 'Win'
    elif winner_code == 2 and player_stats.is_home==False:
        player_stats.match_result = 'Win'
    elif winner_code == 3:
        player_stats.match_result = 'Draw'
    else:
        player_stats.match_result = 'Lose'

    if None in [player_id, event_id]:
        raise ValueError("One of the stats url parameters is None.")
    stats = request_player_event_stats(player_id, event_id)

    if stats.get("error"):
        if stats.get("error").get("code") == 404:
            stats = {"info": f"Player did not play in this game. Evnet Id: {event_id} , Teams: {player_stats.player_team_name} and {player_stats.opponent_team_name} , Game date: {player_stats.event_date}"}
        else:
            raise ValueError(f"URL request failed with code {stats.get('error').get('code')} and message {stats.get('error').get('message')}")
        
    player_stats.stats = stats.get("statistics")

    return player_stats

def obtain_player_event_stats(
        player_name: str,
        event_date: str | Tuple[str,str] | List[str] | None,
        last_k : int | None,
        player_team_name: str | None,
        opponent_team_name: str | None,
        tournament_name: str | None,
        player_id: Optional[int] = None
    ) -> List[PlayerEventStats] | dict | str:
    
    error_messages = []
    
    if player_id is None:
        player_id = get_player_property(player_name=player_name, col_name="PLAYER_ID")
        
        if player_id == False:
            error_messages.append(f"[Tool Error]: Player '{player_name}' not found in the database.")
        elif isinstance(player_id,list):
            if not player_team_name:
                error_messages.append(f"[Tool Error]: Multiple players found in the databse with the name '{player_name}'. Please specify his team.")
            else:
                print("FIND WHICH PLAYER FROM TEAM") # TODO       
        elif isinstance(player_id, Decimal):
            player_id = int(player_id)

    player_team_id = get_player_property(player_name=player_name, col_name="TEAM_ID")
    #player_team_name = get_player_property(player_name=player_name, col_name="TEAM_NAME", dynamo_resource=dynamo_resource)
    
    if opponent_team_name:
        opponent_team_id = get_team_property(team_name=opponent_team_name, col_name="TEAM_ID")
        if opponent_team_id == False:
            error_messages.append(f"[Tool Error]: Team '{opponent_team_name}' not found in the database.")
    else:
        opponent_team_id = None
    
    if tournament_name:
        tournament_id = get_tournament_property(query_value=tournament_name, col_name="TOURNAMENT_ID", gsi=True, key_name="TOURNAMENT_NAME")
        if tournament_id == False:
            error_messages.append(f"[Tool Error]: Team '{tournament_name}' not found in the database.")
    else: 
        tournament_id = None

    if error_messages:
        return error_messages
            
    url_params = create_url_params(
        player_id=player_id,
        event_date=event_date, # can be None
        last_k=last_k, # can be None
        player_team_id=player_team_id,
        player_team_name=player_team_name, # can be None
        opponent_team_id=opponent_team_id, # can be None
        opponent_team_name=opponent_team_name, # can be None
        tournament_id=tournament_id, # can be None
        tournament_name=tournament_name, # can be None
        table_name="dim_events"
    )

    if not url_params:
        return []
    
    player_stats = []
    for param in url_params:
        player_season_stats = create_player_event_stats(player_name=player_name, param=param)
        player_stats.append(player_season_stats)

    return player_stats


