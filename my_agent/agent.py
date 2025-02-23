from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition
from my_agent.utils.state import State
from my_agent.utils.prompt import PROMPT
from my_agent.utils.nodes import Assistant, create_tool_node_with_fallback
from my_agent.utils.tools import calculate_health_metrics
import os
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from langchain_community.tools.tavily_search import TavilySearchResults

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ['TAVILY_API_KEY'] = ''
os.environ["GOOGLE_API_KEY"] = ""


llm = ChatGoogleGenerativeAI(
    model = "gemini-2.0-flash",
    temperature=0,
    max_tokens=5000,
    timeout=30,
    max_retries=2
)

primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            PROMPT,
        ),
        ("placeholder", "{messages}")
    ]
)

tools = [
    calculate_health_metrics,
    TavilySearchResults(max_results=1)
]

assistant_runnable = primary_assistant_prompt | llm.bind_tools(tools=tools, tool_choice="auto")

builder = StateGraph(State)

# Define node: these do the work
builder.add_node("assistant", Assistant(assistant_runnable))
builder.add_node("tools", create_tool_node_with_fallback(tools))

# Define edges: these determine how controls the flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")

# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
logger.info("Graph compiled successfully")