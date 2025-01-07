from pydantic import BaseModel
from typing import Dict, List, Union, Optional, Literal, TypedDict
from dataclasses import dataclass

# INPUT CLASSES

class EventParameters(BaseModel):
    event_date: Union[str,None,List[str]]
    home_team_name: Union[str,None]
    away_team_name: Union[str,None]
    tournament_name: Union[str,None]
    last_k: Union[int,None]

class EventSummaryArgs(BaseModel):
    parameters: List[EventParameters]

class PlayerEventParameters(BaseModel):
    event_date: Union[str,None,List[str]]
    last_k: Union[int,None]
    opponent_team_name: Union[str,None]
    player_team_name: Union[str,None]
    tournament_name: Union[str,None]
    player_name: str

class PlayerEventPerformanceArgs(BaseModel):
    parameters: List[PlayerEventParameters]

class PlayerSeasonParameters(BaseModel):
    player_name: str
    tournament_name: Union[str,None]
    season_year: Union[int,None]
    tournament_country: Union[str,None]

class PlayerSeasonPerformanceArgs(BaseModel):
    parameters: List[PlayerSeasonParameters]
    endpoint: Literal["stats", "ratings", "both"]

@dataclass
class EventSummary:
    home_team: str
    away_team: str
    home_team_squad: dict
    away_team_squad: dict
    comments: List[dict]
    winner: str
    home_team_score: int
    away_team_score: int


@dataclass
class PlayerSeasonRatings:
    player_name: str
    player_id: int = None
    tournament_name: str = None
    tournament_id: int = None
    season_year: int = None
    unique_season_id : int = None
    average_rating: float = None
    average_big_game_rating: float = None
    game_count: int = None
    big_game_count: int = None
    rating_std_dev: float = None
    info: str = None

@dataclass
class PlayerSeasonStats:
    player_name: str
    player_id: int = None
    tournament_name: str = None
    tournament_id: int = None
    season_year: int = None
    unique_season_id : int = None
    stats: dict = None

@dataclass
class PlayerEventStats:
    player_id: int
    player_name: str
    tournament_name: str = None
    event_date : str = None
    opponent_team_name: str = None
    player_team_name: str = None
    is_home : bool = None
    opponent_team_score: int = None
    player_team_score: int = None
    match_result : Literal["Won", "Draw", "Lost"] = None
    stats : dict = None

class ProcessedRating(TypedDict):
    total_games: int
    average_rating: float
    std_dev_rating: float
    average_big_club_rating: float
    big_games_count: int