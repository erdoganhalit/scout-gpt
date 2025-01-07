import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

QUERY_LAMBDA_URL = "https://uy7jwxmzmldtefjhvfqigycigq0yrwpj.lambda-url.eu-north-1.on.aws/"
SCAN_LAMBDA_URL = "https://7tppg6deokrojorjp77aj7bwfa0swntb.lambda-url.eu-north-1.on.aws/"

USE_PROXIES = False
if USE_PROXIES:
    PROXIES = os.getenv("PROXIES")

USER_INFO = """

## How to Use the Football Performance Analysis App :soccer:

This app is designed to help you analyze football player performance on an event level, season level, or specific football matches. Below is a guide on how to interact with the app, the tools available, and the parameters you need to be aware of.

### 1. Focused Analysis Areas

The app is specialized for analyzing the following areas:
- Football player performance at an event level
- Football player performance over a specific season
- Analysis of specific football matches

Please note that questions outside of these topics may result in poorly formulated answers, as the app is optimized for these specific areas.

### 2. How It Works

The app uses different tools to gather data relevant to your question in the background. When you ask a question, an algorithm determines which tool to use and what parameters should be applied to fetch the most accurate data.

### 3. Tool Call Parameters

Once you ask a question, the app will display the relevant parameters in the **Tool Call Parameters** section on the right column. These parameters are essential for refining the data search. 

You have the option to view and manually update the parameters if you wish to refine your query further.


### 4. Understanding the Parameters

#### 4.1. String Match

For string fields, the tool relies on exact matches between your input and the database. Therefore, you will need to input full names of football teams, players, and tournaments. 

*Note that this is the first version of the app and the issue will be fixed in the future.*

##### Example:
❌ "Did **Tottenham** win last night?"
✅ "Did **Tottenham Hotspur** win last night?"

❌ "What happened with the **UCL** games last week?"
✅ "What happened with the **UEFA Champions League** games last week?"

#### 4.2. Null Parameters

 If a parameter is set to **null**, it means that the field is not included as a filter. This indicates that the search is not limited to a specific value.

##### Example:
  - **season_year: null** means no season filter is applied, and data from all seasons will be considered.
  - **tournament_name: null** means no tournament filter is applied, so data from all tournaments will be considered.

#### 4.3 Season Year

 If you ask for a specific **season** the app will automatically extract the year as the input for the **season_year** parameter. Note that **season_year** parameter will be set to the beginning year of the season.
  - **Your question:** "What were Mohamed Salah's stats in the 2023-2024 season?"
  - **season_year** = 2023


## 5. Best Practices for Asking Questions

To ensure you get the best results from the app, please follow these guidelines:
- Use full names for teams and tournaments. For example, ask "Did Manchester City win the Premier League in 2023?" instead of simply "Manchester City" or "Premier League".
- Specify the season or year if you are looking for data from a specific timeframe. For instance, "What was Mbappe's performance in the 2022-2023 season?"
- Ensure your questions are related to player performance, football events, or specific matches for more accurate responses.

If you have any doubts or need further clarification, feel free to consult the parameters and adjust them as needed. The app is designed to provide data-driven insights into the world of football!

"""

logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
