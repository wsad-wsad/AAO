import dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

dotenv.load_dotenv()

model_groq = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=1.0,
    max_tokens=8000,
)

model_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=1.0,
    max_tokens=60000,
    timeout=None,
)
