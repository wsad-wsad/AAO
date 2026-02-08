from langchain_groq import ChatGroq

import requests
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SU_summary_model = ChatGroq(
    api_key=GROQ_API_KEY,
    model="openai/gpt-oss-20b",
    temperature=0.3
)


def SUGW(username:str, user_top_details:str):
    urls = search_web(username, True)
    for url in urls:
        # raw_user_data = url # sementara
        pass


def search_web(username: str, noFalsePositives: bool) -> List[str]:
    try:
        url = f"http://main_go:8000/search-user"
        response = requests.get(url, params={"username": username, "noFalsePositives": noFalsePositives})

        return response.json()

    except requests.ConnectionError as e:
        print(f"Connection error: {e}")
        return []

    except Exception as e:
        print(f"Error user search: {e}")
        return []
    
