from langchain_core.runnables import Runnable
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
from .state import State
import logging
logger = logging.getLogger(__name__)

def handle_tool_error(state) -> dict:
    """
    Function to handle errors that occur during tool execution.
    
    Args:
        state (dict): The current state of the AI agent, which includes messages and tool call details.
    
    Returns:
        dict: A dictionary containing error messages for each tool that encountered an issue.
    """
    # Retrieve the error from current state
    error = state.get("error")

    # Access the tool calls from the last message in the state's message history
    tool_calls = state["message"][-1].tool_calls

    # Return a list of ToolMessage with error details, linked to each tool call ID
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.", # Format the error message
                tool_call_id=tc["id"] # Associate the error message with the corresponding tool call ID
            )
            for tc in tool_calls # Iterate over each tool call in the message
        ]
    }
def create_tool_node_with_fallback(tools: list) -> dict:
    """
    Function to create tool node with fallback error handling
    
    Args:
        tools (list): List of tools to be added to the tool node
        
    Returns:
        dict: A tool node that uses fallback behavior to handle errors
    """
    # Create a ToolNode with the provided tools and attach a fallback mechanism
    # If an error occurs, it will invoke the handle_tool_error function to manage the error
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], # Use a lambda function to wrap the error handler
        exception_key="error", # Specify that this fallback is for handling errors
    )

class Assistant:
    def __init__(self, runnalbe: Runnable):
        self.runnable = runnalbe
    
    def __call__(self, state: State) -> dict:
        """Execute the assistant with the current state.

        Args:
            state (State): Current state with messages.

        Returns:
            dict: Updated state with assistant response.
        """
        logger.info("Assistant node invoked")
        result = self.runnable.invoke(state)
        return {"messages": [result]}
