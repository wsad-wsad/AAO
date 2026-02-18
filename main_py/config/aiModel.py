import os

import dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

dotenv.load_dotenv()

model_groq = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
)

model_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.7,
    max_tokens=5020,
    api_key=os.getenv("GEMINI_API_KEY"),
)
