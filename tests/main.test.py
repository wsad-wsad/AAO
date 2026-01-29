import os

import dotenv
import requests

dotenv.load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
NETLAS_API_KEY = os.environ.get("NETLAS_API_KEY")


def google_search(query):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx=30d33e1be3b154e97&q={query}"
        response = requests.get(url)
        data = response.json()
        print(data)
        return data
    except Exception as e:
        print(f"Error Google: {e}")
        return None


def netlas_search(query):
    try:
        url = "https://app.netlas.io/api/host/"

        headers = {
            "Authorization": f"Bearer {NETLAS_API_KEY}",
            "Accept": "application/json",
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        print(data)
        return data
    except Exception as e:
        print(f"Error Netlas: {e}")
        return None


netlas_search("google.com")
google_search("jokowi")
