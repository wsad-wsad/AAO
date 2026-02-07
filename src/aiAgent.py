from deep_translator import GoogleTranslator
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from config.aiModel import model_groq
from config.prompt import SYSTEM_PROMPT
from config.responseFormat import ResponseFormat
from config.tool import (
    google_search,
    holehe_search,
    netlas_search,
    phone_lookup,
    wappalyzer,
)

agent = create_agent(
    model=model_groq,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        netlas_search,
        google_search,
        holehe_search,
        phone_lookup,
        wappalyzer,
    ],
    response_format=ToolStrategy(ResponseFormat),
)


def input_req(input: str):
    print("--- Run Agent ---")

    input_translated = GoogleTranslator(source="auto", target="en").translate(input)
    response = agent.invoke(
        {"messages": [{"role": "user", "content": input_translated}]},
        config={"configurable": {"thread_id": "1"}},
    )

    return response["structured_response"]
