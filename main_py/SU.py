from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    JsonCssExtractionStrategy,
    LLMConfig
)

from pathlib import Path
import re
import json
from urllib.parse import urlparse
import requests
from typing import List
import os
from dotenv import load_dotenv
import toon

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SU_web_info_model = ChatGroq(
    api_key=GROQ_API_KEY,
    model="groq/compound-mini",
)

SU_summary_model = ChatGroq(
    api_key=GROQ_API_KEY,
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.3
)

def search_web(username: str, noFalsePositives: bool) -> List[str]:
    url = f"http://localhost:8000/search-user"
    response = requests.get(url, params={"username": username, "noFalsePositives": noFalsePositives}, headers={"Content-Type": "application/json"})

    return response.json()

def parse_json_web_pattern(data: dict):
    """
    Parse the JSON data to extract user identity and metrics."""
    identity = {k.replace('user_identity_', ''): v for k, v in data.items() if k.startswith('user_identity_')}
    metrics = {k.replace('user_metrics_', ''): v for k, v in data.items() if k.startswith('user_metrics_')}
    return identity, metrics

async def parse_base_url(url: str, username: str, just_domain: bool = False):
    url = urlparse(url)
    domain = url.netloc
    
    domain = re.sub(r'^www\.', '', domain)  # Remove 'www.'
    domain = re.sub(rf'^{re.escape(username)}', '', domain)     # blm di beresin full 
    
    # This turns 'my-site.co.uk' into 'my-site-co-uk'
    domain = re.sub(r'[^a-zA-Z0-9]', '-', domain)
    domain = re.sub(r'-+', '-', domain).strip('-') # Remove multiple hyphens
    return domain.lower()

async def generate_pattern(url: str, pattern_file: Path, crawler: AsyncWebCrawler):
    llm_config = LLMConfig(
        provider="gemini/gemini-3-flash-preview",
        api_token=GEMINI_API_KEY,
        temperature=1.0
    )
    
    result = await crawler.arun(url)
    if not result.success:
        print("crawler error on generate pattern, URL: ", url)
        return {}

    pattern = await JsonCssExtractionStrategy.agenerate_schema(
        html=str(result.fit_html),
        query=pattern_prompt,
        llm_config=llm_config
    )

    web_info = await SU_web_info_model.ainvoke(
        web_info_prompt(url)
    )
    web_info = web_info.content

    if pattern != {} and web_info:
        json.dump({"pattern": pattern, "web_info": web_info}, pattern_file.open("w"), indent=2)
        return {"pattern": pattern, "web_info": web_info}
    elif pattern == {}:
        print("pattern not generated")
    else:
        print("web info not generated")

    return {}

async def urls_search(urls: List[str], username: str):
    pattern_dir = Path("/app/pattern-data")

    datas = []
    web_info = []
    async with AsyncWebCrawler() as crawler:
        for url in urls:
            base_url = await parse_base_url(url, username)
            pattern_file = pattern_dir / f"{base_url}.json"

            if pattern_file.exists():
                with pattern_file.open() as f:
                    pattern_file_data = json.load(f)
            else:
                pattern_file_data = await generate_pattern(url, pattern_file, crawler)
                if pattern_file_data == {}:
                    print("pattern not found")
                    continue
            
            strategy = JsonCssExtractionStrategy(pattern_file_data["pattern"])
            config = CrawlerRunConfig(
                extraction_strategy=strategy,
                exclude_all_images=True,
                exclude_external_images=True
                )

            result = await crawler.arun(url, config)

            if result.success:
                data = json.loads(result.extracted_content)
                if data and pattern_file_data["web_info"]:
                    datas.append(data)
                    web_info.append(pattern_file_data["web_info"])

    return datas, web_info

async def SUGW(username:str, user_top_details:str = None):
    urls = search_web(username, True)[4:6]
    scraped_datas, web_info = await urls_search(urls, username)

    summarize_data_list = []
    for i, data in enumerate(scraped_datas):
        user_identity, user_metrics = parse_json_web_pattern(data)
        @tool
        def get_web_info(index=i)->str:
            """Use this function if you need to get information for the web"""
            return web_info[index]
        
        # make temp model for each data
        SU_summary_model_temp = SU_summary_model.model_copy()
        SU_summary_model_temp.bind_tools([get_web_info])

        summarize_data = await SU_summary_model_temp.ainvoke([summary_prompt, HumanMessage(f"Input: {toon.encode(user_metrics)}")])
        summarize_data_list.append(summarize_data.content)

        SU_summary_model_temp = None

    return summarize_data_list


pattern_prompt = """
# Act as a web scraping engineer. Generate a JSON schema for JsonCssExtractionStrategy to extract user-centric data from the provided HTML.

# Objective: Map relevant data to a specific naming convention using two primary categories.

# Instructions for Schema Generation:
1. Categorization & Prefixes: You must use the following two prefixes for every key in your JSON, followed by a descriptive name for the data point. The format must be [prefix]_[specific_data_name]:
- user_identity_... (Use ONLY for name, full_name, gender, age, email)
- user_metrics_... (Use for all other data: counts, scores, streaks, elo, activity levels, followers, following, posts, or any other numeric/status metric)
2. Dynamic Logic: Do not use a static template. Analyze the HTML structure to find the elements that correspond to these categories. If a category is missing data, simply omit it or use an empty array/null.
3. Robust Selectors: Prioritize id, data-attributes, aria-labels, or semantic tags (<article>, <header>) over generic, deep-nested class structures.
4. Exclusions: Exclude all global UI boilerplate (navigation, login, cookies, terms) and all the images.

## Example Pattern: 
- If you find a 'Full Name', name it user_identity_full_name.
- If you find a 'Chess Elo', name it user_metrics_chess_elo.
- If you find a 'Activity', name it user_metrics_streak.

# remember this: if the html data doesn't contain any user data, or the data quality is poor, return an empty object {}
"""

def web_info_prompt(url: str):
    return f"""
# Act as a web research assistant. Your task is to extract general information from the base domain of the provided URL: {url}.

# Instructions:
1. Normalize the URL: Ignore any specific sub-pages, paths, or user identifiers; extract information based on the root domain/website home.
2. Analysis: Identify and summarize the following:
    - Purpose: A single sentence defining what the website/company does.
    - Target Audience: The sector they serve or the general audience.
3. Format:
- Include only essential facts needed to identify the the website/company.
- Make it each 1 sentence.
- Do not include promotional jargon or filler text.
"""

summary_prompt = SystemMessage("""
# Your task is to summarize TOON scraped user data for semantic embedding.

# Instructions:
1. Output 1 continuous string that only contains the summary. NO formatting/newlines.
2. Concisely list key identifiers, data values, and keywords.
3. Use `get_web_info()` ONLY if JSON lacks entity context.
""")