from langchain_core.tools import tool
from typing import Dict, List, Union, Optional, Literal, Tuple
import requests
from config import *
from tools.modules import *
import requests
import time
from datetime import datetime

from dataclasses import dataclass

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
            return None

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
        event_date: str | Tuple[str,str] | List[str] | None,
        last_k : int | None, 
        home_team_name: str | None,
        away_team_name: str | None,
        home_team_id: int | None,
        away_team_id: int | None,
        tournament_name: str | None,
        tournament_id: int | None,
        table_name:str
        ) -> List[dict]:

    # Reference the DynamoDB table dim_unique_seasons
    payload = {
        "table_name": table_name,
        "filter": {
            "type": "logical",
            "operation": "and",
            "subfilters": []
        }
    }

    # Add team-related conditions (home vs. away logic)
    if home_team_id:
        if away_team_id:
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
                                    "value": home_team_id
                                },
                                {
                                    "type": "atomic",
                                    "attribute": "AWAY_TEAM_ID",
                                    "operation": "eq",
                                    "value": away_team_id
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
                                    "value": away_team_id
                                },
                                {
                                    "type": "atomic",
                                    "attribute": "AWAY_TEAM_ID",
                                    "operation": "eq",
                                    "value": home_team_id
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
                            "value": home_team_id
                        },
                        {
                            "type": "atomic",
                            "attribute": "AWAY_TEAM_ID",
                            "operation": "eq",
                            "value": home_team_id
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
                raise ValueError(f"Event date list or tuple should have exactly two values. One start date, one end date. This one has {len(event_date)} values.")
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
        if tournament_name:
            event["TOURNAMENT_NAME"] = tournament_name
        else:
            event["TOURNAMENT_NAME"] = get_tournament_property(query_value=event.get("TOURNAMENT_ID"), col_name="TOURNAMENT_NAME", key_name="TOURNAMENT_ID", gsi=False)
        
        url_params.append(event)

    return url_params

def request_event_data(event_id, endpoint):
    url=f"https://www.sofascore.com/api/v1/event/{event_id}/{endpoint}"
    if USE_PROXIES:
        for i, proxy in enumerate(PROXIES):
            try:
                start_time = time.time()  # Start the timer
                response = requests.get(url, proxies={"http": proxy}, timeout=10)
                response_time = time.time() - start_time  # Calculate response time
                if response.status_code == 200:
                    print(f"Endpoint {endpoint} - Success with proxy number {i+1} : {proxy} in {response_time:.2f} seconds")
                    return response.json()
            except Exception as e:
                time.sleep(2)  # Add delay to avoid bans
        raise Exception("All proxies failed!")
    else:
        response = requests.get(url, timeout=10)
        return response.json()

def get_event_comments(event_id: int, summary: bool):
    response = request_event_data(event_id=event_id, endpoint='comments')
    if summary:
        important_comment_types = ["penaltyAwarded", "penaltyLost", "penaltyScored", "scoreChange", "videoAssistantReferee", "redCard"]
    else:
        important_comment_types = ["penaltyAwarded", "penaltyLost", "penaltyScored", "post", "scoreChange", "substitution", "videoAssistantReferee", "yellowCard", "redCard"]

    important_comments = []

    if not response.get("comments"):
        return important_comments

    for comment in response["comments"]:
        if comment["type"] in important_comment_types:
            important_comments.append(
                {
                    "text": comment["text"], 
                    "minute": comment["time"], 
                    "incident_type": comment["type"]
                }
            )
    return important_comments

def get_event_lineups(event_id):
    response = request_event_data(event_id=event_id, endpoint='lineups')

    lineups = {"home": {"starting": [], "bench": [], "missing": []},
               "away": {"starting": [], "bench": [], "missing": []}}

    if not response.get('home'):
        return lineups
    
    for side in ["home", "away"]:
        for player in response[side]['players']:
            if player['substitute']:
                lineups[side]["bench"].append(player['player']['name'])
            else:
                lineups[side]["starting"].append(player['player']['name'])

        if response[side].get('missingPlayers'):
            for player in response[side]['missingPlayers']:
                lineups[side]["missing"].append(player['player']['name'])

    return lineups

def create_event_data(param: dict, summary: bool) -> EventSummary:
    event_id = param['EVENT_ID']
    home_team=param["HOME_TEAM_NAME"]
    away_team=param["AWAY_TEAM_NAME"]
    home_team_score=param["HOME_SCORE"]
    away_team_score=param["AWAY_SCORE"]

    wc = param['WINNER_CODE']
    if wc:
        if int(wc) == 1:
            winner = home_team
        elif int(wc) == 2:
            winner = away_team
        elif int(wc) == 3:
            winner = 'Draw'
        else:
            raise ValueError("Winner Code should be 1, 2, or 3")
    else:
        winner = 'Unknown'

    comments = get_event_comments(event_id=event_id, summary=summary)
    lineups = get_event_lineups(event_id)

    return EventSummary(
        home_team=param["HOME_TEAM_NAME"],
        away_team=param["AWAY_TEAM_NAME"],
        home_team_squad=lineups['home'],
        away_team_squad=lineups['away'],
        comments=comments,
        winner=winner,
        home_team_score=home_team_score,
        away_team_score=away_team_score
    )


        