import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
# from langchain.llms import Ollama
# from langchain_community.llms import Ollama
from langchain_ollama import OllamaLLM

# llama = Ollama(model="llama2-uncensored")
mistral = OllamaLLM(model="mistral:instruct")


# Load environment variables from .env file
load_dotenv()

USER_ID = "RealEstateClient"
session_service = InMemorySessionService()
APP_NAME = "real_estate_advisor_app"
SESSION_ID = "session_001"

from real_estate_agent import real_estate_advisor, call_agent_async, create_session
from email_agent import e_mail_agent
from tools import save_user_preference, retrieve_user_preferences, find_properties,store_email,retrieve_emails,get_email_by_id





runner = Runner(
    agent=[real_estate_advisor, e_mail_agent],
    app_name=APP_NAME,
    session_service=session_service,
)


async def call_agent_async(query: str, user_id: str, session_id: str):
    print(f"\n>>> User ({user_id}): {query}")
    content = types.Content(role="user", parts=[types.Part(text=query)])
    setattr(save_user_preference, "user_id", user_id)
    setattr(retrieve_user_preferences, "user_id", user_id)
    # Set user_id for tool functions
    setattr(store_email, "user_id", user_id)
    setattr(retrieve_emails, "user_id", user_id)
    setattr(get_email_by_id, "user_id", user_id)
    setattr(find_properties, "user_id", user_id)

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_response = event.content.parts[0].text
            print(f"<<< Assistant: {final_response}")
            return final_response

    return "No response received."


async def interactive_chat():
    print("--- Starting Interactive Email RAG Agent ---")
    print("You can store and retrieve emails.")
    print("Example storage: store email from 'John <j.doe@example.com>' to 'Jane <jane@example.com>' with date '2023-01-01', subject 'Meeting' and body 'Hi, team.'")
    print("Example retrieval: what are the emails about 'Meeting'?")
    print("Type 'quit' to end the session.")
    while True:
        user_query = input("\n> ")
        if user_query.lower() in ["quit", "exit"]:
            print("Ending session. Goodbye!")
            break
        await call_agent_async(query=user_query, user_id=USER_ID, session_id=SESSION_ID)


async def create_session():
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )



if __name__ == "__main__":
    if (
        not os.getenv("GOOGLE_API_KEY")
        or os.getenv("GOOGLE_API_KEY") == "YOUR_GOOGLE_API_KEY_HERE"
    ):
        print(
            "ERROR: Please set your GOOGLE_API_KEY environment variable to run this script."
        )
    else:
        asyncio.run(create_session())
        asyncio.run(interactive_chat())
