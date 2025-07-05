import os
import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from google.adk.models.lite_llm import LiteLlm
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.exceptions import DocumentNotFoundException

# Load environment variables from .env file
load_dotenv()

USER_ID = os.getenv("USER_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or None
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or None
API_KEY = OPENROUTER_API_KEY if OPENROUTER_API_KEY else GEMINI_API_KEY
if not API_KEY:
    raise ValueError("Please set your OPENROUTER_API_KEY or GEMINI_API_KEY environment variable to run this script.")

MODEL = "gemini-2.5-flash"

if OPENROUTER_API_KEY:
    MODEL = LiteLlm(
        model="openrouter/google/gemini-2.5-flash",
        api_key=API_KEY,
    )

# --- Couchbase Memory Class ---
class CouchbaseMemory:
    def __init__(
        self,
        conn_str,
        username,
        password,
        bucket_name,
        scope_name="email",
        collection_name="memory",
    ):
        self.cluster = Cluster(
            conn_str, ClusterOptions(PasswordAuthenticator(username, password))
        )
        self.bucket = self.cluster.bucket(bucket_name)
        self.scope = self.bucket.scope(scope_name)
        self.collection = self.scope.collection(collection_name)
        print("[Memory System] Connected to Couchbase Capella")

    def _doc_id(self, user_id: str):
        return f"user::{user_id}"

    def add(self, user_id: str, category: str, data: str):
        doc_id = self._doc_id(user_id)
        try:
            doc = self.collection.get(doc_id).content_as[dict]
        except DocumentNotFoundException:
            doc = {}

        doc.setdefault(category, [])
        if data not in doc[category]:
            doc[category].append(data)
            self.collection.upsert(doc_id, doc)
            print(
                f"[Memory System] Saved data for user '{user_id}' in category '{category}': '{data}'"
            )
        return True

    def search_by_category(self, user_id: str, category: str) -> list:
        doc_id = self._doc_id(user_id)
        try:
            doc = self.collection.get(doc_id).content_as[dict]
            results = doc.get(category, [])
        except DocumentNotFoundException:
            results = []
        print(
            f"[Memory System] Retrieved {len(results)} items from category '{category}' for user '{user_id}'."
        )
        return results


# --- Replace with your Capella credentials ---
COUCHBASE_CONN_STR = os.getenv("COUCHBASE_CONN_STR")
COUCHBASE_USERNAME = os.getenv("COUCHBASE_USERNAME")
COUCHBASE_PASSWORD = os.getenv("COUCHBASE_PASSWORD")
COUCHBASE_BUCKET = os.getenv("COUCHBASE_BUCKET")

persistent_data = CouchbaseMemory(
    conn_str=COUCHBASE_CONN_STR,
    username=COUCHBASE_USERNAME,
    password=COUCHBASE_PASSWORD,
    bucket_name=COUCHBASE_BUCKET,
    scope_name="agent",  # match your setup
    collection_name="memory",  # match your setup
)


def store_email(
    from_sender: str,
    to_recipient: str,
    date: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
) -> dict:
    """Saves an email to memory.

    Args:
        from_sender: The sender of the email (e.g., 'John Doe <john.doe@example.com>').
        to_recipient: The recipient of the email.
        date: The date of the email (e.g., 'YYYY-MM-DD').
        subject: The subject of the email.
        body: The content of the email.
        cc: The CC recipients of the email (optional).

    Returns:
        A dictionary with the status of the operation.
    """
    user_id = getattr(store_email, "user_id", USER_ID)
    email_data = (
        f"From: {from_sender}\n"
        f"To: {to_recipient}\n"
        f"Date: {date}\n"
        f"CC: {cc or ''}\n"
        f"Subject: {subject}\n"
        f"Body: {body}"
    )
    persistent_data.add(user_id=user_id, category="emails", data=email_data)
    return {"status": "success", "message": "Email stored successfully."}


def retrieve_emails(query: Optional[str] = None) -> dict:
    """Retrieves emails from memory that match a query.

    Args:
        query: The search term to filter emails. If empty, all emails are returned.

    Returns:
        A dictionary containing the list of matching emails.
    """
    user_id = getattr(retrieve_emails, "user_id", USER_ID)
    all_emails = persistent_data.search_by_category(user_id=user_id, category="emails")

    if not query:
        return {"status": "success", "emails": all_emails, "count": len(all_emails)}

    matching_emails = [email for email in all_emails if query.lower() in email.lower()]

    print(
        f"INFO: Found {len(matching_emails)} emails matching '{query}'"
    )

    return {"status": "success", "emails": matching_emails, "count": len(matching_emails)}


rag_agent = Agent(
    name="rag_agent",
    model=MODEL,
    description="A helpful RAG agent that remembers email conversations and can help with replying to emails, and also answer questions about the communications.",
    instruction="""
You are a friendly and efficient RAG agent for managing emails.

Email Management Workflow:
1. To save an email, use the `store_email` tool. You must provide `from_sender`, `to_recipient`, `date`, `subject`, and `body`. The `cc` field is optional.
2. To find emails, use the `retrieve_emails` tool. You can provide an optional `query` to search through the content of all stored emails. If you omit the query, you will get all emails.
3. Use the retrieved emails to answer questions or compose new messages.
""",
    tools=[store_email, retrieve_emails],
)


session_service = InMemorySessionService()
APP_NAME = "email_rag_app"
SESSION_ID = "session_001"

runner = Runner(
    agent=rag_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def call_agent_async(query: str, user_id: str, session_id: str):
    print(f"\n>>> User ({user_id}): {query}")
    content = types.Content(role="user", parts=[types.Part(text=query)])
    # Set user_id for tool functions
    setattr(store_email, "user_id", user_id)
    setattr(retrieve_emails, "user_id", user_id)

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
        asyncio.run(create_session())
        asyncio.run(interactive_chat())
