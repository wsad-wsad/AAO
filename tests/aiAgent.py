import json
import os
from typing import Any, Dict, Optional

import dotenv
from google import genai

from until.prompt import SYSTEM_INSTRUCTION, prompt, prompt_report
from until.tool import netlas_search  # google_searc

dotenv.load_dotenv()


class AiAgent:
    def __init__(self, target):
        self.target = target

    def _parse(self, text):
        return str(text).strip().replace("```json", "").replace("```", "")

    def _mikir_ai(self) -> Dict[str, Any]:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[prompt.format(target=self.target)],
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "max_output_tokens": 65536,
            },
        )
        print("--- RAW RESPONSE AI (ANALISIS) ---")
        print(response.text)
        print("------------------------------------")
        return json.loads(self._parse(response.text))

    def scan(self):
        result = self._mikir_ai()

        if "netlas_search" in result["tools"]:
            return netlas_search(self.target)
        else:
            return None

    def analisis(self, data_mentah: Optional[Any] = None) -> Dict[str, Any]:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt_report.format(data_mentah=data_mentah)],
            config={
                "max_output_tokens": 65536,
            },
        )
        print("--- RAW RESPONSE AI (ANALISIS) ---")
        print(response.text)
        print("------------------------------------")

        return json.loads(self._parse(response.text))

    def run(self):
        tool_name = self._mikir_ai().get("tools", [None])[0]

        while tool_name:
            if tool_name == "netlas_search":
                data = netlas_search(self.target)
            else:
                data = None

            report = self.analisis(data)

            if not report.get("lanjut"):
                return report

            tool_name = report.get("tools")

        return {"message": "Tidak ada tool yang dipilih."}
