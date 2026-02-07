from dataclasses import dataclass

import dotenv
from deep_translator import GoogleTranslator
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver

from until.prompt import SYSTEM_PROMPT
from until.tool import google_search, holehe_search, netlas_search, phone_lookup

dotenv.load_dotenv()


# Define context schema
@dataclass
class Context:
    """Custom runtime context schema."""

    user_id: str


model_groq = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=1.0,
    max_tokens=8000,
)

model_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=1.0,
    max_tokens=60000,
    timeout=None,
)


# Define response format
@dataclass
class ResponseFormat:
    """Response schema for the agent."""

    target: str
    tool_used: str
    summary: str
    detailed_report: str


# Set up memory
checkpointer = InMemorySaver()

# Create agent
agent = create_agent(
    model=model_groq,
    system_prompt=SYSTEM_PROMPT,
    tools=[netlas_search, google_search, holehe_search, phone_lookup],
    context_schema=Context,
    response_format=ToolStrategy(ResponseFormat),
    checkpointer=checkpointer,
)


# Run agent
def input_req(input: str):
    print("--- Run Agent ---")

    input_translated = GoogleTranslator(source="auto", target="en").translate(input)
    response = agent.invoke(
        {"messages": [{"role": "user", "content": input_translated}]},
        config={"configurable": {"thread_id": "1"}},
        context=Context(user_id="1"),
    )

    return response["structured_response"]
