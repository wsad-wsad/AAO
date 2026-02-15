import os
from typing import List

import dotenv
import requests
from langchain_google_genai import ChatGoogleGenerativeAI

dotenv.load_dotenv()

SU_summary_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.7,
    max_tokens=4380,
    api_key=os.getenv("GEMINI_API_KEY"),
)


def SUGW(username: str, user_top_details: str):
    urls = search_web(username, True)
    for url in urls:
        # raw_user_data = url # sementara
        pass


def search_web(username: str, noFalsePositives: bool) -> List[str]:
    try:
        url = f"http://main_go:8000/search-user"
        response = requests.get(
            url, params={"username": username, "noFalsePositives": noFalsePositives}
        )

        return response.json()

    except requests.ConnectionError as e:
        print(f"Connection error: {e}")
        return []

    except Exception as e:
        print(f"Error user search: {e}")
        return []
