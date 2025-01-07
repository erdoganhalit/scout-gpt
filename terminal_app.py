from graph.graph import Subgraph, MainGraph
from tools.tools import EVENT_PERFORMANCE_TOOL, SEASON_PERFORMANCE_TOOL, EVENT_SUMMARY_TOOL
from graph.config import (
    ANALYZE_GAME_TOOL_CALLER_SYSTEM_MESSAGE,
    ANALYZE_PLAYER_TOOL_CALLER_SYSTEM_MESSAGE,
    ROUTER_SYSTEM_MESSAGE,
    ROUTER_MODEL_NAME,
)

def main():
    # Create subgraphs
    player_analyze_subgraph = Subgraph(
        tools=[EVENT_PERFORMANCE_TOOL, SEASON_PERFORMANCE_TOOL],
        name='analyze-player',
        tool_caller_system_message=ANALYZE_PLAYER_TOOL_CALLER_SYSTEM_MESSAGE
    )

    game_analyze_subgraph = Subgraph(
        tools=[EVENT_SUMMARY_TOOL],
        name='analyze-game',
        tool_caller_system_message=ANALYZE_GAME_TOOL_CALLER_SYSTEM_MESSAGE
    )

    # Create the MainGraph
    main_graph = MainGraph(
        subgraphs=[player_analyze_subgraph, game_analyze_subgraph],
        router_model_name=ROUTER_MODEL_NAME,
        router_system_message=ROUTER_SYSTEM_MESSAGE,
    )

    config = {"configurable": {"thread_id": "1"}}

    print("Welcome! I can assist you with analyzing football games and players. Type 'TERMINATE CONVERSATION' to end.")

    while True:
        # Get user input
        user_input = input("\nYour question: ").strip()

        # Check if the user wants to terminate the conversation
        if user_input.upper() == "TERMINATE CONVERSATION":
            print("Goodbye! Have a great day!")
            break

        # Process the user input through the MainGraph
        main_graph.process_message(user_input=user_input, config=config)

if __name__ == "__main__":
    main()
