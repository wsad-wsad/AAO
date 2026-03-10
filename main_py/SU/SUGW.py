from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    JsonCssExtractionStrategy,
    LLMConfig
)

import numpy as np
from nomic import embed
from sklearn.neighbors import NearestNeighbors

from pathlib import Path
import re
import json
from urllib.parse import urlparse
import requests
from typing import List
import os
from dotenv import load_dotenv
import toon

from SU.AI_prompt import web_info_prompt, pattern_prompt, summary_prompt
from SU.name_matching import is_same_person

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

def _search_web(username: str, noFalsePositives: bool) -> List[str]:
    url = f"http://localhost:8000/search-user"
    response = requests.get(url, params={"username": username, "noFalsePositives": noFalsePositives}, headers={"Content-Type": "application/json"})

    return response.json()

def _parse_json_web_pattern(data: dict):
    """
    Parse the JSON data to extract user identity and metrics.
    """
    identity = {k.replace('user_identity_', ''): v for k, v in data.items() if k.startswith('user_identity_')}
    metrics = {k.replace('user_metrics_', ''): v for k, v in data.items() if k.startswith('user_metrics_')}
    return identity, metrics

async def _parse_base_url(url: str, username: str):
    url = urlparse(url)
    domain = url.netloc
    
    domain = re.sub(r'^www\.', '', domain)  # Remove 'www.'
    domain = re.sub(rf'^{re.escape(username)}', '', domain)     # blm di beresin full 
    
    # This turns 'my-site.co.uk' into 'my-site-co-uk'
    domain = re.sub(r'[^a-zA-Z0-9]', '-', domain)
    domain = re.sub(r'-+', '-', domain).strip('-') # Remove multiple hyphens
    return domain.lower()

async def _generate_pattern(url: str, pattern_file: Path, crawler: AsyncWebCrawler):
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

async def _urls_search(urls: List[str], username: str):
    pattern_dir = Path("/app/pattern-data")

    datas = []
    web_info = []
    async with AsyncWebCrawler() as crawler:
        for url in urls:
            base_url = await _parse_base_url(url, username)
            pattern_file = pattern_dir / f"{base_url}.json"

            if pattern_file.exists():
                with pattern_file.open() as f:
                    pattern_file_data = json.load(f)
            else:
                pattern_file_data = await _generate_pattern(url, pattern_file, crawler)
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

def _data_similarity(query: str, data: List[str], threshold: float = 0.5):
    data_embed = embed.text(
        data,
        model='nomic-embed-text-v1.5',
        task_type='search_document',
        inference_mode='local'
    )
    data_embed = np.array(data_embed['embeddings'])
    data_embed = data_embed.reshape(-1, 1)

    query_embed = embed.text(
        [query],
        model='nomic-embed-text-v1.5',
        task_type='search_document',
        inference_mode='local'
    )
    query_embed = np.array(query_embed['embeddings'])
    query_embed = query_embed.reshape(1, -1)

    print(f"query_embed shape: {query_embed.shape}")
    print(f"data_embed shape: {data_embed.shape}")

    neigh = NearestNeighbors(radius=threshold, metric='cosine')
    neigh.fit(data_embed)

    distances, indices = neigh.radius_neighbors(query_embed)

    out = []
    for i in indices.flatten():
        out.append({"data": data[i],"distance": distances[0][i]})

    return out, data

async def SUGW(username:str, user_top_details:str, full_name: str = None):
    """
    Generate a summary of a user's web presence.
    """
    # urls = _search_web(username, True)
    urls = [
        "https://www.strava.com/athletes/Dafi",
        "https://beacons.ai/Dafi",
        "https://www.figma.com/@Dafi",
        "https://Dafi.substack.com",
        "https://www.roblox.com/user.aspx?username=Dafi"]
    scraped_datas, web_info = await _urls_search(urls, username)

    summarize_data_list = []
    for i, data in enumerate(scraped_datas):
        user_identity, user_metrics = _parse_json_web_pattern(data[0])
        
        if full_name:
            if user_identity.get("full_name") or user_identity.get("name"):
                # check is there name or full_name
                if user_identity.get("full_name"):
                    name = user_identity["full_name"]
                elif user_identity.get("name") and not user_identity.get("full_name"):
                    name = user_identity["name"]
                
                if not is_same_person(full_name, name, 0.75):
                    continue

        @tool
        def _get_web_info(index=i)->str:
            """Use this function if you need to get information for the web"""
            return web_info[index]
        
        # make temp model for each data
        SU_summary_model_temp = SU_summary_model.model_copy()
        SU_summary_model_temp.bind_tools([_get_web_info])

        summarize_data = await SU_summary_model_temp.ainvoke([SystemMessage(summary_prompt), HumanMessage(toon.encode(user_metrics))])
        summarize_data_list.append(summarize_data.content.strip())

        SU_summary_model_temp = None

    return {"result": _data_similarity(user_top_details, summarize_data_list)}