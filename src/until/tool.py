import os
import subprocess

import dotenv
import requests
from langchain.tools import tool

dotenv.load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
NETLAS_API_KEY = os.environ.get("NETLAS_API_KEY")


@tool
def google_search(query: str):
    """
    Execute a search query against the Google Custom Search API.
    """
    try:
        url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx=30d33e1be3b154e97&q={query}"
        response = requests.get(url)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error Google: {e}")
        return None


@tool
def netlas_search(query: str):
    """
    Execute a search query against the Netlas.io database to find internet-connected devices.
    """
    try:
        url = f"https://app.netlas.io/api/host/{query}"

        headers = {
            "Authorization": f"Bearer {NETLAS_API_KEY}",
            "Accept": "application/json",
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error Netlas: {e}")
        return None


@tool
def holehe_search(input: str):
    """
    Enter your email to find out if you are registered on any site.
    """
    try:
        result = subprocess.run(
            ["holehe", input], capture_output=True, text=True, check=True
        )
        return result.stdout

    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
