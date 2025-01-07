from tools.tools import SEASON_PERFORMANCE_TOOL, EVENT_PERFORMANCE_TOOL
from graph.utils import count_tokens
from langchain_openai import ChatOpenAI
from typing import Annotated, Any, Literal, Union, List
from pydantic import BaseModel
from langchain_core.messages import (AIMessage, AnyMessage, ToolCall, ToolMessage, SystemMessage, HumanMessage)
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import RemoveMessage
from config import OPENAI_API_KEY
# Configuration defaults
from graph.config import (
    TOOL_CALLER_MODEL_NAME,
    ANSWER_GENERATOR_MODEL_NAME,
    TOOL_CALLER_TEMPERATURE,
    ANSWER_GENERATOR_TEMPERATURE,
    ANALYZE_GAME_TOOL_CALLER_SYSTEM_MESSAGE,
    ANSWER_GENERATOR_SYSTEM_MESSAGE,
    TOKEN_THRESHOLD
)

class Subgraph:
    def __init__(
        self,
        name: str,
        tools: list,
        tool_caller_system_message: str,
        interrupt : List[str] | bool,
        tool_caller_model: str = TOOL_CALLER_MODEL_NAME,
        tool_caller_temperature: float = TOOL_CALLER_TEMPERATURE,
        answer_generator_model: str = ANSWER_GENERATOR_MODEL_NAME,
        answer_generator_temperature: float = ANSWER_GENERATOR_TEMPERATURE,
        answer_generator_system_message: str = ANSWER_GENERATOR_SYSTEM_MESSAGE,
    ):
        """
        Initializes the AnalyzeComparePlayersGraph with LLM configurations for tool caller and answer generator.

        Args:
            tools (list): List of tools that will be used by the subgraph
            tool_caller_model (str): Model name for the tool caller LLM.
            tool_caller_temperature (float): Temperature value for the tool caller LLM.
            answer_generator_model (str): Model name for the answer generator LLM.
            answer_generator_temperature (float): Temperature value for the answer generator LLM.
            tool_caller_system_message (str): System message for the tool caller node.
            answer_generator_system_message (str): System message for the answer generator node.
        """
        # Initialize LLMs
        self.name = name
        self.tool_caller_llm = ChatOpenAI(model=tool_caller_model, temperature=tool_caller_temperature, api_key=OPENAI_API_KEY)
        self.answer_generator_llm = ChatOpenAI(model=answer_generator_model, temperature=answer_generator_temperature, api_key=OPENAI_API_KEY)

        # System messages
        self.tool_caller_system_message = tool_caller_system_message
        self.answer_generator_system_message = answer_generator_system_message

        # Tools setup
        self.analyze_tools = tools
        self.analyze_tools_node = ToolNode(tools=self.analyze_tools)

        # Bind tools to tool caller LLM
        self.llm_with_tools = self.tool_caller_llm.bind_tools(tools=self.analyze_tools, strict=True)

        # Define graph state and builder
        class State(TypedDict):
            messages: Annotated[list, add_messages]

        self.graph_builder = StateGraph(State)

        self.memory = MemorySaver()

        # Nodes to interrupt before
        self.interrupt = interrupt

        # Build the graph
        self._build_graph()

        self.graph = self.compile_graph()

    def _build_graph(self):
        """Builds the state graph with nodes and edges."""
        # Add nodes
        self.graph_builder.add_node("tool_caller", self._tool_caller)
        self.graph_builder.add_node("analyze_tools", self.analyze_tools_node)
        self.graph_builder.add_node("answer_generator", self._answer_generator)

        # Add edges
        self.graph_builder.add_conditional_edges("tool_caller", self._tool_caller_edge_condition)
        self.graph_builder.add_conditional_edges("analyze_tools", self._tool_edge_condition)

        # Set entry and finish points
        self.graph_builder.set_entry_point("tool_caller")
        self.graph_builder.set_finish_point("answer_generator")

    def _tool_edge_condition(
        self,
        state: Union[list[AnyMessage], dict[str, Any], BaseModel],
        messages_key: str = "messages",
    ) -> Literal["analyze_tools", "answer_generator"]:
        if isinstance(state, list):
            last_message = state[-1]
        elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
            last_message = messages[-1]
        elif messages := getattr(state, messages_key, []):
            last_message = messages[-1]
        else:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")
        
        if isinstance(last_message, ToolMessage) and '[Tool Error]' not in last_message.content: # Correct Tool Message is retrieved
            return "answer_generator"
        elif isinstance(last_message, HumanMessage): # When AI Message with Tool call is manually deleted.
            return "answer_generator"
        else: # All other scenarios, run the Tool Node again.
            return "analyze_tools"

    def _tool_caller_edge_condition(
        self,
        state: Union[list[AnyMessage], dict[str, Any], BaseModel],
        messages_key: str = "messages",
    ) -> Literal["analyze_tools", "__end__"]:
        """
        Conditional function to determine whether to proceed to analyze tools or end.

        Args:
            state: The current state of the graph.
            messages_key: The key for retrieving messages from the state.

        Returns:
            Literal["analyze_tools", "__end__"]: Next node identifier.
        """
        if isinstance(state, list):
            last_message = state[-1]
        elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
            last_message = messages[-1]
        elif messages := getattr(state, messages_key, []):
            last_message = messages[-1]
        else:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")
        if isinstance(last_message, HumanMessage):
            return "__end__"
        elif hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
            return "analyze_tools"
        return "__end__"

    def _tool_caller(self, state: dict):
        """
        Node function to handle tool caller logic.

        Args:
            state: The current state of the graph.

        Returns:
            dict: Updated state with messages.
        """
        system_message = SystemMessage(content=self.tool_caller_system_message)
        state["messages"].insert(-1, system_message)
        response = self.llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def _answer_generator(self, state: dict):
        """
        Node function to handle answer generation logic.

        Args:
            state: The current state of the graph.

        Returns:
            dict: Updated state with messages.
        """
        system_message = SystemMessage(content=self.answer_generator_system_message)
        state["messages"].append(system_message)
        return {"messages": [self.answer_generator_llm.invoke(state["messages"])]}

    def compile_graph(self):
        """
        Compiles and returns the state graph.

        Returns:
            StateGraph: Compiled graph instance.
        """

        if self.interrupt:
            return self.graph_builder.compile(
                checkpointer=self.memory,
                interrupt_before=self.interrupt
            )
        else:
            return self.graph_builder.compile(
                checkpointer=self.memory
            )
    
    def _get_messages_to_remove(self, config):
        threshold = TOKEN_THRESHOLD
        snapshot = self.graph.get_state(config)
        messages = snapshot.values["messages"]
        total_content = ''
        for msg in messages:
            total_content += msg.content
        token_count = count_tokens(total_content)
        print("current total token: " + str(token_count))

        if token_count <= threshold:
            return []
        
        current_token_count = 0
        messages_to_delete = []

        # Iterate from the beginning to collect messages until the difference is covered
        for msg in messages:
            msg_token_count = count_tokens(msg.content)
            current_token_count += msg_token_count
            messages_to_delete.append(RemoveMessage(id=msg.id))

            # Check if the current token count exceeds the difference
            if token_count - current_token_count <= threshold:
                break

        return messages_to_delete
    
    def check_for_feedback(self, config, app_state):
        snapshot = self.graph.get_state(config)
        existing_message = snapshot.values["messages"][-1]

        if existing_message.tool_calls:
            new_tool_call = existing_message.tool_calls[0].copy()
            warning_message = f"""
            WARNING: System message:
            Software will use the following parameters to retrieve relevant data:
            
            {new_tool_call['args']['parameters']}
            
            If you want to change these parameters, respond with the desired values in the structure of the dictionary.
            If not, leave the input blank and continue.
            """
            print(warning_message)
            app_state.feedback_pending = True  # Set flag to indicate feedback is needed
            app_state.pending_tool_call = new_tool_call  # Save tool call for later use
            return app_state, warning_message  # Return the message to display
        else:
            app_state.feedback_pending = False  # No feedback required
            return app_state, ""

    def update_tool_message(self, tool_call_feedback, app_state):
        config = app_state.config
        snapshot = self.graph.get_state(config)
        existing_message = snapshot.values["messages"][-1]        
        
        if isinstance(existing_message, AIMessage):
            if tool_call_feedback == {}:
                for msg in snapshot.values['messages'][::-1]:
                    if isinstance(msg, SystemMessage):
                        last_system_message = msg
                        break
                delete_msgs = [RemoveMessage(id=existing_message.id), RemoveMessage(id=last_system_message.id)]
                self.graph.update_state(config=config, values={"messages": delete_msgs}, as_node='analyze_tools')
                return app_state
            else:
                new_tool_call = existing_message.tool_calls[0].copy()
                new_tool_call['args']['parameters'] = [tool_call_feedback]
                new_message = AIMessage(
                    content=existing_message.content,
                    tool_calls=[new_tool_call],
                    # Important! The ID is how LangGraph knows to REPLACE the message in the state rather than APPEND this messages
                    id=existing_message.id,
                )
                self.graph.update_state(config, {"messages": [new_message]})
                app_state.config = config
                return app_state
        elif isinstance(existing_message, ToolMessage):
            previous_message = snapshot.values["messages"][-2]
            self.graph.update_state(config, {"messages": RemoveMessage(id=existing_message.id)})
            new_tool_call = previous_message.tool_calls[0].copy()
            new_tool_call['args']['parameters'] = [tool_call_feedback]
            new_message = AIMessage(
                content=previous_message.content,
                tool_calls=[new_tool_call],
                # Important! The ID is how LangGraph knows to REPLACE the message in the state rather than APPEND this messages
                id=previous_message.id,
            )
            self.graph.update_state(config, {"messages": [new_message]})
            app_state.config = config
            return app_state
    
    def stream_graph_updates(self, user_input: str, config: dict):
        #state["messages"].append(("user", user_input))
        if user_input:
            stream_input = {"messages": [("user", user_input)]}
        else:
            stream_input = None

        snapshot = self.graph.get_state(config)
        

        events = self.graph.stream(
            input=stream_input, config=config, stream_mode="values"
        )

        for event in events:
            for messages in event.values():
                last_message = messages[-1]
                if isinstance(last_message, AIMessage):
                    if last_message.content != '':
                        print("Assistant: ", last_message.content)
                        return last_message.content
                elif isinstance(last_message, ToolMessage):
                    if '[Tool Error]' in last_message.content:
                        return last_message.content
    
class MainGraph:
    def __init__(
        self,
        subgraphs: List[Subgraph],
        router_model_name: str,
        router_system_message: str
    ):
        """
        Initialize the MainGraph that handles routing between subgraphs.

        Args:
            subgraphs (List[Subgraph]): List of Subgraph instances to route between.
            router_model_name (str): Model name for the router LLM.
            router_system_message (str): System message for the router node.
        """
        self.subgraphs = subgraphs
        self.router_llm = ChatOpenAI(model=router_model_name, temperature=0.0, api_key=OPENAI_API_KEY)
        self.router_system_message = router_system_message

    def _route_message(self, user_input: str) -> Subgraph:
        """
        Use the router LLM to decide which subgraph to use based on user input.

        Args:
            user_input (str): The user's input message.

        Returns:
            Subgraph: The selected subgraph for processing.
        """
        system_message = SystemMessage(content=self.router_system_message)
        messages = [system_message, ("user", user_input)]
        response = self.router_llm.invoke(messages)

        # Match the response to a subgraph
        for subgraph in self.subgraphs:
            if subgraph.name.lower() in response.content.lower():
                return subgraph

        raise ValueError("Unable to route message to a subgraph. Check router logic or messages.")

    def process_message(self, user_input: str, config: dict, app_state):
        """
        Process the user's message by routing it to the appropriate subgraph.
        
        Args:
            user_input (str): The user's input message.
            config (dict): Configuration dictionary for the graph.
            state (dict): Gradio state dictionary for feedback handling.

        Returns:
            str: The AI's response or feedback prompt.
        """
        # Route the message to the correct subgraph
        selected_subgraph = self._route_message(user_input)

        # Process the input through the selected subgraph
        response = selected_subgraph.stream_graph_updates(user_input=user_input, config=config)

        # Check for feedback from the user
        app_state, feedback_message = selected_subgraph.check_for_feedback(config, app_state)
        if feedback_message:
            app_state.selected_subgraph = selected_subgraph
            return feedback_message  # Return warning to display in the UI with a bool True indicating response is Feedback
        # Stream the updated response
        response = selected_subgraph.stream_graph_updates(user_input=None, config=config)

        remove_old_msgs = selected_subgraph._get_messages_to_remove(config=config)
        if remove_old_msgs:
            selected_subgraph.graph.update_state(config, remove_old_msgs)

        return response