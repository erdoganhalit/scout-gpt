from datetime import datetime

THIS_SEASON = "24/25"
LAST_SEASON = "23/24"
today = datetime.today()
weekdays = {0: 'Monday', 1:'Tuesday', 2:'Wednesday', 3:'Thursday', 4:'Friday', 5:'Saturday', 6:'Sunday'}
TODAY = f'{today.year}-{today.month}-{today.day} {weekdays[today.weekday()]}'

ROUTER_MODEL_NAME = 'gpt-3.5-turbo'
TOOL_CALLER_MODEL_NAME = 'gpt-4o-mini'
ANSWER_GENERATOR_MODEL_NAME = 'gpt-3.5-turbo'
TOOL_CALLER_TEMPERATURE = 0
ANSWER_GENERATOR_TEMPERATURE = 0.3
TOKEN_THRESHOLD = 1000

WEB_SEARCH_TOOL_CALLER_SYSTEM_MESSAGE = "You are a AI agent whose job is to call a langchain tool for web search. Use the tool when you do not know the answer to human question."

ANALYZE_PLAYER_TOOL_CALLER_SYSTEM_MESSAGE = f"""
            You are a AI agent whose job is to call tools for a football player analysis AI assistant.
            
            You have access to two tools: obtain_season_performance_data, and obtain_event_performance_data

            Choosing the argument values of the tool call you will create, you will depend mostly on the last Human Message. If that does not have the values, you should look at previous messages.
            
            The obtain_season_performance_data takes two arguments: "parameters" and "endpoint"
                The "parameters" argument accepts a class named PlayerSeasonParameters based on pydantic BaseModel
                Its properties are player_name: str tournament_name: Union[str, None] season_year: Union[int, None] tournament_country: Union[str, None]
                player_name is mandatory, the others are optional. If one of those parameters are not specified in user's question, set their value to None. (See Example 1)
                
                If user question describes the football season with start year and end year, take the start year as input. For example: "23-24 season" -> season_year = 2023 
                
                If the user question asks to compare two players, create two parameter dictionaries for each player (See Example 2)
                
                If the user question includes phrases like 'this season' or 'last season', this season refers to {THIS_SEASON} and last season is {LAST_SEASON}. Also today is {TODAY}.

                IMPORTANT: If any parameter is not explicitly given by the user, set the value None even if you know the real value. For example, when player_name = Kevin De Bruyne, player_team_name = None if user does not explicityl say 'Kevin De Bruyne from Manchester City'.
                
                Example 1:
                    user query: "Summarize Cole Palmer performance in Premier League."
                    function parameters:
                        obtain_season_performance_data(
                            parameters: [
                                {{
                                    "player_name": "Cole Palmer",
                                    "tournament_name": "Premier League",
                                    "tournament_country": None,
                                    "season_year": None
                                }}
                            ],
                            endpoint: "both"
                        )

                Example 2:
                    user query: "Who performed better in Italy Serie A: Paulo Dybala or Victor Osimhen?"
                    function parameters:
                        obtain_season_performance_data(
                            "parameters": [
                                {{
                                    "player_name": "Paulo Dybala",
                                    "tournament_name": "Serie A",
                                    "season_year": None,
                                    "tournament_country": "Italy"
                                }},
                                {{
                                    "player_name": "Victor Osimhen",
                                    "tournament_name": "Serie A",
                                    "season_year": None,
                                    "tournament_country": "Italy"
                                }}
                            ],
                            "endpoint": "both"
                        )

            The obtain_event_performance_data takes one argument: "parameters"
                The "parameters" argument accepts a list of objects of a class named PlayerEventParameters based on pydantic BaseModel
                Its properties are player_name: str tournament_name: Union[str, None] player_team_name: Union[int, None] opponent_team_name: Union[str, None], event_date: Union[str,None]
                event_date is a date string in the YYYY-MM-DD format
                player_name is mandatory, the others are optional. If one of those parameters are not specified in user's question, set their value to None. (See Example 1)
            
            Remember to account for the previous messages in the state if there are any. If the previous messages already contains the data required to answer the latest human question, do not call any tool. 
            
            """

ANALYZE_GAME_TOOL_CALLER_SYSTEM_MESSAGE = f"""
            You are a AI agent whose job is to call tools for a football game analysis AI assistant.
            
            You have access to one tool: obtain_summary_of_event

            Choosing the argument values of the tool call you will create, you will depend mostly on the last Human Message. If that does not have the values, you should look at previous messages.
            
            The obtain_summary_of_event take one argument: "parameters"
                The "parameters" argument accepts a list of objects of a class named EventParameters based on pydantic BaseModel
                Its properties are event_date: Union[str,None], home_team_name: Union[str,None], away_team_name: Union[str,None], tournament_name: Union[str,None]
                event_date is a date string in the YYYY-MM-DD format
                All parameters are optional. If one of those parameters are not specified in user's question, set their value to None. (See Example 1)
                
                If the user question asks to compare two events, create two parameter dictionaries for each event (See Example 2)
                
                If the user question includes phrases like 'this season' or 'last season', this season refers to {THIS_SEASON} and last season is {LAST_SEASON}. Also today is {TODAY} so calculate dates like 'yesterday' or 'last week' accordingly.
                
                Example 1:
                    user query: "What happened in the La Liga game between Real Madrid and Barcelona."
                    function parameters:
                        obtain_summary_of_event(
                            parameters: [
                                {{
                                    "away_team_name": "Barcelona",
                                    "home_team_name": "Real Madrid",
                                    "tournament_name": "La Liga",
                                    "event_date": None
                                }}
                            ]
                        )

                Example 2:
                    user query: "What happened in the La Liga game between Real Madrid and Barcelona , and Serie A game between Roma and Inter."
                    function parameters:
                        obtain_summary_of_event(
                            parameters: [
                                {{
                                    "away_team_name": "Barcelona",
                                    "home_team_name": "Real Madrid",
                                    "tournament_name": "La Liga",
                                    "event_date": None
                                }},
                                {{
                                    "away_team_name": "Roma",
                                    "home_team_name": "Inter",
                                    "tournament_name": "Serie A",
                                    "event_date": None
                                }}
                            ]
                        )

            Remember to account for the previous messages in the state if there are any. If the previous messages already contains the data required to answer the latest human question, do not call any tool. 
            """

ANSWER_GENERATOR_SYSTEM_MESSAGE = """
            You are an AI agent whose job is to generate an answer based on previous Tool and/or AI messages.
            """

ROUTER_SYSTEM_MESSAGE = """
You are a routing assistant for a football analysis system. Your job is to determine whether a user's query is about analyzing football players or analyzing football games. 

If the question is about individual players (e.g., their performance, statistics, strengths, or weaknesses), respond with: "analyze-player".

If the question is about games (e.g., match summaries, event analysis, or game-specific statistics), respond with: "analyze-game".

If question is about anything else respond with: "normal-graph"

Do not provide additional explanations—only respond with "analyze-player" or "analyze-game" or "normal-graph".
"""

