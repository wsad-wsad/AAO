import json
import os
from typing import Any, Dict

import dotenv
from google import genai

from until.prompt import prompt, prompt_report
from until.tool import netlas_search  # google_searc

dotenv.load_dotenv()


class AiAgent:
    def __init__(self, target):
        self.target = target

    def parse(self, text):
        return str(text).strip().replace("```json", "").replace("```", "")

    def mikir_ai(self) -> Dict[str, Any]:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[prompt.format(target=self.target)],
            config={
                "max_output_tokens": 65536,
            },
        )
        return json.loads(self.parse(response.text))

    def scan_target(self):
        result = self.mikir_ai()

        if "netlas_search" in result["tools"]:
            return netlas_search(self.target)
        else:
            return None

    def generate_report(self, data_mentah):
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[prompt_report.format(data_mentah=data_mentah)],
            config={
                "max_output_tokens": 65536,
            },
        )
        return json.loads(self.parse(response.text))
