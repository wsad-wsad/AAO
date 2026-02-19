from config.aiModel import model_gemini
from config.prompt import SYSTEM_PROMPT
from config.responseFormat import ResponseFormat
from config.tool import (
    google_search,
    holehe_search,
    netlas_search,
    pddikti_all,
    phone_lookup,
    search_mhs_by_name_or_nim,
    wappalyzer,
)
from deep_translator import GoogleTranslator
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

agent = create_agent(
    model=model_gemini,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        netlas_search,
        google_search,
        holehe_search,
        phone_lookup,
        wappalyzer,
        pddikti_all,
        search_mhs_by_name_or_nim,
    ],
    response_format=ToolStrategy(ResponseFormat),
)


def input_req(input: str):
    print("agent running")
    try:
        input_translated = GoogleTranslator(source="auto", target="en").translate(input)
        response = agent.invoke(
            {"messages": [{"role": "user", "content": input_translated}]},
        )
        return response["structured_response"].dict()

    except Exception as e:
        return str(e)
