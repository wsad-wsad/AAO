import json
import os
from typing import Any, Dict

import dotenv
from google import genai

# from until.mikir_ai import mikir_ai
from until.prompt import prompt
from until.tool import netlas_search  # google_searc

dotenv.load_dotenv()


class AiAgent:
    def __init__(self, target):
        self.target = target

    def mikir_ai(self) -> Dict[str, Any]:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[prompt, self.target],
        )
        print(f"[===INFO===]{response.text}")
        return json.loads(str(response.text))

    def scan_target(self):
        result = self.mikir_ai()

        if "netlas_search" in result["tools"]:
            return netlas_search(self.target)
        # if "google_search" in result["tools"]:
        #     return google_search(self.target)
        # note: googlenya error saat ini pake netlas dulu
