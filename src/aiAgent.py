from dataclasses import dataclass

import dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver

from until.prompt import SYSTEM_PROMPT
from until.tool import netlas_search

dotenv.load_dotenv()


# Define context schema
@dataclass
class Context:
    """Custom runtime context schema."""

    user_id: str


model = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.8,
    max_tokens=8000,
    max_retries=2,
)


# Define response format
@dataclass
class ResponseFormat:
    """Response schema for the agent."""

    target: str
    summary: str
    detailed_report: str


# Set up memory
checkpointer = InMemorySaver()

# Create agent
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[netlas_search],
    context_schema=Context,
    response_format=ToolStrategy(ResponseFormat),
    checkpointer=checkpointer,
)


# Run agent
def input(input: str):
    print("--- Testing Agent ---")
    response = agent.invoke(
        {"messages": [{"role": "user", "content": input}]},
        config={"configurable": {"thread_id": "1"}},
        context=Context(user_id="1"),
    )

    return response["structured_response"]
