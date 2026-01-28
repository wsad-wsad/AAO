import json
import os
import dotenv

import asyncio
import aiofiles
import requests
from google import genai

from until.prompt import prompt

dotenv.load_dotenv()


class AiAgent:
    def __init__(self, target):
        self.target = target

    def mikir_ai(self):
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[
                prompt,
            ],
        )
        return response.text
