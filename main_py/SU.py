from langchain_groq import ChatGroq
from crawl4ai import AsyncWebCrawler

import re
import asyncio
import requests
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SU_summary_model = ChatGroq(
    api_key=GROQ_API_KEY,
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.3
)

def SUGW(username:str, user_top_details:str = None):
    urls = search_web(username, True)
    raw_scraped_datas = asyncio.run(urls_search(urls))

    clean_scraped_datas = []
    for scraped_data in raw_scraped_datas:
        clean_scraped_datas.append(clean_markdown(scraped_data))

    # data_summary = []
    # for scraped_data in scraped_datas:
    #     data = SU_summary_model.invoke(f"Summarize this data: {scraped_data}")
    #     data_summary.append(data)
    
    return {"raw_scraped_data": raw_scraped_datas, "clean_scraped_datas": clean_scraped_datas}

def clean_markdown(md: str) -> str:
    # --- 1. Remove common UI boilerplate ---
    ui_noise_patterns = [
        r"(?i)^(home\s*>\s*)+.*$",                     # breadcrumbs
        r"(?i)^(login|sign in|sign up|register).*$",   # login prompts
        r"(?i)^(follow us|share on|share this).*$",    # social buttons
        r"(?i)^(privacy policy|terms of service).*$",  # footer links
        r"(?i)^(cookies?|cookie settings).*$",         # cookie banners
        r"(?i)^(©|\(c\)|copyright).*$",                # copyright lines
        r"(?i)^\[?advertisement\]?$",                  # advertisement labels
        r"(?i)^sponsored content.*$",                  # sponsor label
    ]

    for pattern in ui_noise_patterns:
        md = re.sub(pattern, "", md, flags=re.MULTILINE)

    # --- 2. Remove image-only lines ---
    md = re.sub(r"^!\[[^\]]*\]\([^)]+\)\s*$", "", md, flags=re.MULTILINE)

    # --- 3. Collapse multiple blank lines (keep max 1) ---
    md = re.sub(r"\n{3,}", "\n\n", md)

    # --- 4. Remove trailing spaces ---
    md = re.sub(r"[ \t]+$", "", md, flags=re.MULTILINE)

    # --- 5. Trim start and end ---
    md = md.strip()

    return md


async def urls_search(urls: List[str]) -> List[str]:
    async with AsyncWebCrawler() as crawler:
        datas = await crawler.arun_many(urls)

        result = []
        for data in datas:
            if data.success and data.markdown:
                result.append(data.markdown)
    
    return result

# func untuk ngejalanin gosearch dengan http req
# memberikan list[url: str]
def search_web(username: str, noFalsePositives: bool) -> List[str]:
    url = f"http://localhost:8000/search-user"
    response = requests.get(url, params={"username": username, "noFalsePositives": noFalsePositives}, headers={"Content-Type": "application/json"})

    return response.json()
