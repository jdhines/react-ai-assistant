"""
This is the main entry point for the agent.
It defines the workflow graph, state, tools, nodes and edges.
"""
import os
from dotenv import dotenv_values
from typing_extensions import Literal
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langgraph.prebuilt.tool_node import ToolNode
from copilotkit import CopilotKitState
from .mongo_checkpointer import MongoCheckpointSaver


class AgentState(CopilotKitState):
    """
    Here we define the state of the agent

    In this instance, we're inheriting from CopilotKitState, which will bring in
    the CopilotKitState fields. We're also adding a custom field, `language`,
    which will be used to set the language of the agent.
    """
    proverbs: list[str] = []
    # your_custom_agent_state: str = ""


@tool
def get_weather(location: str):
    """
    Get the weather for a given location.
    """
    return f"The weather for {location} is 70 degrees."

# @tool
# def your_tool_here(your_arg: str):
#     """Your tool description here."""
#     print(f"Your tool logic here")
#     return "Your tool response here."


tools = [
    get_weather
    # your_tool_here
]


async def chat_node(state: AgentState, config: RunnableConfig) -> Command[Literal["tool_node", "__end__"]]:
    """
    Standard chat node based on the ReAct design pattern. It handles:
    - The model to use (and binds in CopilotKit actions and the tools defined above)
    - The system prompt
    - Getting a response from the model
    - Handling tool calls

    For more about the ReAct design pattern, see:
    https://www.perplexity.ai/search/react-agents-NcXLQhreS0WDzpVaS4m9Cg
    """
    # Debug: Print state and config to understand what's available
    print(f"💬 chat_node called with state keys: {list(state.keys())}")
    print(f"💬 chat_node config: {config}")
    print(f"💬 chat_node config.configurable: {config.get('configurable', {})}")

    # Check if user_id is available in the state or config
    user_id = None
    if hasattr(state, 'user_id'):
        user_id = state.user_id
        print(f"💬 Found user_id in state: {user_id}")

    config_user_id = config.get('configurable', {}).get('user_id')
    if config_user_id:
        print(f"💬 Found user_id in config.configurable: {config_user_id}")
        user_id = config_user_id

    if not user_id:
        print(f"💬 No user_id found, checking other locations...")
        # Check other possible locations
        for key in ['userId', 'user', 'homeAccountId']:
            if config.get('configurable', {}).get(key):
                print(
                    f"💬 Found {key} in config.configurable: {config['configurable'][key]}")
            if hasattr(state, key) and getattr(state, key):
                print(f"💬 Found {key} in state: {getattr(state, key)}")

    # If no user_id is available, we can't save conversations properly
    if not user_id:
        print(f"💬 ⚠️  WARNING: No user_id found! Conversations won't be saved properly.")
        # We could either:
        # 1. Generate a random user_id for this session
        # 2. Skip persistence
        # 3. Raise an error
        # For now, let's generate a session-specific ID
        import uuid
        user_id = f"anonymous-{str(uuid.uuid4())[:8]}"
        print(f"💬 Generated anonymous user_id: {user_id}")
        config.setdefault('configurable', {})['user_id'] = user_id

    # Load environment variables
    env_vars = dotenv_values()
    os.environ.update(env_vars)

    # 1. Define the model
    model = AzureChatOpenAI(
        model=os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION",
                              "2025-01-01-preview"),
        temperature=0.2
    )

    # 2. Bind the tools to the model
    model_with_tools = model.bind_tools(
        [
            *state["copilotkit"]["actions"],
            get_weather,
            # your_tool_here
        ],

        # 2.1 Disable parallel tool calls to avoid race conditions,
        #     enable this for faster performance if you want to manage
        #     the complexity of running tool calls in parallel.
        parallel_tool_calls=False,
    )

    # 3. Define the system message by which the chat model will be run
    system_message = SystemMessage(
        content=f"You are a helpful assistant. Talk in {state.get('language', 'english')}."
    )

    # 4. Run the model to generate a response
    response = await model_with_tools.ainvoke([
        system_message,
        *state["messages"],
    ], config)

    # 5. Check for tool calls in the response and handle them. We ignore
    #    CopilotKit actions, as they are handled by CopilotKit.
    if isinstance(response, AIMessage) and response.tool_calls:
        actions = state["copilotkit"]["actions"]

        # 5.1 Check for any non-copilotkit actions in the response and
        #     if there are none, go to the tool node.
        if not any(
            action.get("name") == response.tool_calls[0].get("name")
            for action in actions
        ):
            return Command(goto="tool_node", update={"messages": response})

    # 6. We've handled all tool calls, so we can end the graph.
    return Command(
        goto=END,
        update={
            "messages": response
        }
    )

# Define the workflow graph
workflow = StateGraph(AgentState)
workflow.add_node("chat_node", chat_node)
workflow.add_node("tool_node", ToolNode(tools=tools))
workflow.add_edge("tool_node", "chat_node")
workflow.set_entry_point("chat_node")

# Note: The workflow is exported for server.py to compile with checkpointer
# The graph compilation happens in server.py's lifespan function
