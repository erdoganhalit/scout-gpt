import gradio as gr
import re
import json
from graph.graph import Subgraph, MainGraph
from tools.tools import EVENT_PERFORMANCE_TOOL, SEASON_PERFORMANCE_TOOL, EVENT_SUMMARY_TOOL
from graph.config import (
    ANALYZE_GAME_TOOL_CALLER_SYSTEM_MESSAGE,
    ANALYZE_PLAYER_TOOL_CALLER_SYSTEM_MESSAGE,
    WEB_SEARCH_TOOL_CALLER_SYSTEM_MESSAGE,
    ROUTER_SYSTEM_MESSAGE,
    ROUTER_MODEL_NAME,
)
from config import USER_INFO
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchResults


# Initialize Graphs
player_analyze_subgraph = Subgraph(
    tools=[EVENT_PERFORMANCE_TOOL, SEASON_PERFORMANCE_TOOL],
    name='analyze-player',
    tool_caller_system_message=ANALYZE_PLAYER_TOOL_CALLER_SYSTEM_MESSAGE,
    interrupt=['analyze_tools']
)

game_analyze_subgraph = Subgraph(
    tools=[EVENT_SUMMARY_TOOL],
    name='analyze-game',
    tool_caller_system_message=ANALYZE_GAME_TOOL_CALLER_SYSTEM_MESSAGE,
    interrupt=['analyze_tools']
)

normal_subgraph = Subgraph(
    tools=[DuckDuckGoSearchResults()],
    name="normal-graph",
    tool_caller_system_message=WEB_SEARCH_TOOL_CALLER_SYSTEM_MESSAGE,
    interrupt=False
)

main_graph = MainGraph(
    subgraphs=[player_analyze_subgraph, game_analyze_subgraph, normal_subgraph],
    router_model_name=ROUTER_MODEL_NAME,
    router_system_message=ROUTER_SYSTEM_MESSAGE,
)

# State to manage feedback
# State management
class GradioState():
    def __init__(self):
        self.feedback_pending = False
        self.pending_tool_call = None
        self.selected_subgraph = None
        self.parameters = []
        self.config = {"configurable": {"thread_id": "1"}}
        
gr_state = GradioState()

def handle_user_input(user_message: str, chat_history: list):
    """Process user input and update sidebar values"""
    #config = {"configurable": {"thread_id": "1"}}

    response = main_graph.process_message(user_input=user_message, config=gr_state.config, app_state=gr_state)
    if gr_state.feedback_pending:
        # Parse parameters from state
        gr_state.parameters = gr_state.pending_tool_call["args"]["parameters"]
        tool_call_updated = json.dumps(gr_state.parameters[0], indent=4)  # Format as JSON with indentation
        # Display the JSON string and make it visible
        chat_history.append((user_message, "I've parsed your request. You can modify the values in the sidebar."))
        return "", chat_history, gr.update(value=tool_call_updated, visible=True, interactive=True)  # Update the JSON Textbox
    else:
        chat_history.append((user_message, response))
        return "", chat_history, gr.update(value='', visible=False, interactive=True)


def update_tool_call(chat_history: list, tool_params_feedback: str):
    """Process updated values from sidebar"""
    if tool_params_feedback == '':
        updated_params = {}
    else:
        try:
            updated_params = json.loads(tool_params_feedback)  # Parse the updated JSON input
        except (ValueError, TypeError, json.JSONDecodeError):
            chat_history.append((None, "Please enter valid JSON"))
        
    #config = {"configurable": {"thread_id": "1"}}
    selected_subgraph = gr_state.selected_subgraph
    if selected_subgraph:
        new_gr_state = selected_subgraph.update_tool_message(app_state=gr_state, tool_call_feedback=updated_params)
        response = selected_subgraph.stream_graph_updates(user_input=None, config=new_gr_state.config)
        chat_history.append((None, response))
    
    if '[Tool Error]' in response:
        return chat_history, gr.update(value=tool_params_feedback, interactive=True, visible=True) , gr_state
    
    else:
        gr_state.feedback_pending = False
        gr_state.pending_tool_call = None
        gr_state.selected_subgraph = None
        gr_state.parameters = []
            
        return chat_history, gr.update(visible=False)

def create_app(gr_state):
    with gr.Blocks(css="""
        #sidebar {
            max-height: 700px;
            overflow-y: auto;
        }
    """) as demo:
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown(USER_INFO, elem_id="sidebar")
            # Chat Interface
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="ScoutGPT", height=700)
                msg = gr.Textbox(label="Ask your question")

            # Sidebar (always visible)
            with gr.Column(scale=1):
                gr.Markdown("## Tool Call Parameters")
                # Initialize a single textbox for JSON output
                tool_params_textbox = gr.Textbox(label="Tool Call JSON", visible=False, interactive=True, lines=16)
                update_btn = gr.Button("Update")

        # Handle initial user input
        msg.submit(
            handle_user_input,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot, tool_params_textbox]
        )

        # Handle update button click
        #if tool_params_textbox.visible:
        update_btn.click(
            update_tool_call,
            inputs=[chatbot, tool_params_textbox],
            outputs=[chatbot, tool_params_textbox]
        )

    return demo

if __name__ == "__main__":
    app = create_app(gr_state)
    app.launch()
