from tools.functions import obtain_summary_of_event, obtain_event_performance_data, obtain_season_performance_data
from tools.modules import EventParameters, EventSummary, PlayerEventParameters, PlayerSeasonParameters
from config import logger
from test.utils import log_test_results

def test_event_summary(parameters):
    output = obtain_summary_of_event(
        parameters=parameters
    )

    return output

def test_event_performance(parameters):
    output = obtain_event_performance_data(
        parameters=parameters
    )
    return output

def test_season_performance(parameters, endpoint):
    output = obtain_season_performance_data(
        parameters=parameters,
        endpoint=endpoint
    )

    return output

event_summary_inputs = [
    EventParameters(
        home_team_name="Galatasaray",
        away_team_name="Kayserispor",
        event_date="2024-12-22",
        last_k=None,
        tournament_name=None
    ),
    EventParameters(
        home_team_name="Galatasaray",
        away_team_name=None,
        event_date=None,
        last_k=3,
        tournament_name=None
    ),
    EventParameters(
        home_team_name="Galatasaray",
        away_team_name=None,
        event_date=None,
        last_k=3,
        tournament_name="Trendyol Süper Lig"
    ),
    EventParameters(
        home_team_name="Real Madrid",
        away_team_name="Barcelona",
        event_date=None,
        last_k=3,
        tournament_name=None
    ),
    EventParameters(
        home_team_name=None,
        away_team_name=None,
        event_date=None,
        last_k=10,
        tournament_name="UEFA Champions League"
    ),
    EventParameters(
        home_team_name="Fenerbahçe",
        away_team_name=None,
        event_date=["2024-10-30", "2024-11-30"],
        last_k=None,
        tournament_name="Trendyol Süper Lig"
    ),
    EventParameters(
        home_team_name=None,
        away_team_name=None,
        event_date="2024-12-11",
        last_k=None,
        tournament_name="UEFA Champions League"
    )
]

event_performance_inputs = [
    PlayerEventParameters(
        event_date="2024-11-22",
        player_name="Victor Osimhen",
        player_team_name="Galatasaray",
        opponent_team_name="Kayserispor",
        tournament_name="Trendyol Süper Lig",
        last_k=None
    ),
    PlayerEventParameters(
        event_date=None,
        player_name="Victor Osimhen",
        player_team_name="Galatasaray",
        opponent_team_name="Kayserispor",
        tournament_name="Trendyol Süper Lig",
        last_k=None
    ),
    PlayerEventParameters(
        event_date="2024-11-22",
        player_name="Victor Osimhen",
        player_team_name=None,
        opponent_team_name=None,
        tournament_name=None,
        last_k=None
    ),
    PlayerEventParameters(
        event_date=["2024-11-25", "2024-12-25"],
        player_name="Victor Osimhen",
        player_team_name=None,
        opponent_team_name=None,
        tournament_name=None,
        last_k=None
    ),
    PlayerEventParameters(
        event_date=None,
        player_name="Victor Osimhen",
        player_team_name=None,
        opponent_team_name=None,
        tournament_name="Trendyol Süper Lig",
        last_k=3
    ),
    PlayerEventParameters(
        event_date=None,
        player_name="Victor Osimhen",
        player_team_name=None,
        opponent_team_name=None,
        tournament_name=None,
        last_k=3
    ),
    PlayerEventParameters(
        event_date="2024-11-22",
        player_name="Victor Osimhen",
        player_team_name="Galatasaray",
        opponent_team_name="Kayserispor",
        tournament_name="Trendyol Süper Lig",
        last_k=None
    ),
    PlayerEventParameters(
        event_date="2024-11-20",
        player_name="Victor Osimhen",
        player_team_name="Galatasaray",
        opponent_team_name="Kayserispor",
        tournament_name="Trendyol Süper Lig",
        last_k=None
    )
]

season_performance_inputs = [
    PlayerSeasonParameters(
        player_name="Victor Osimhen",
        tournament_name="Trendyol Süper Lig",
        season_year=2024,
        tournament_country="Turkey"
    ),
    PlayerSeasonParameters(
        player_name="Victor Osimhen",
        tournament_name="Trendyol Süper Lig",
        season_year=None,
        tournament_country=None
    ),
    PlayerSeasonParameters(
        player_name="Victor Osimhen",
        tournament_name=None,
        season_year=2024,
        tournament_country=None
    ),
    PlayerSeasonParameters(
        player_name="Mauro Icardi",
        tournament_name=None,
        season_year=2023,
        tournament_country=None
    )
]

#event_summary_output = test_event_summary(parameters=event_summary_inputs)
event_performance_output = test_event_performance(parameters=event_performance_inputs)
#season_performance_output = test_season_performance(parameters=season_performance_inputs, endpoint='both')


#log_test_results(
#    logger=logger,
#    file_path="test/results/event_summary_test_result.txt",
#    output=event_summary_output
#)
log_test_results(
    logger=logger,
    file_path = "test/results/event_performance_test_result.txt",
    output=event_performance_output
)
#log_test_results(
#    logger=logger,
#    file_path = "test/results/season_performance_test_result.txt",
#    output=season_performance_output
#)

