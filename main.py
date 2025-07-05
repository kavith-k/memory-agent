import os
import asyncio
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.exceptions import DocumentNotFoundException

# Load environment variables from .env file
load_dotenv()


USER_ID = "RealEstateClient"


# --- Couchbase Memory Class ---
class CouchbaseMemory:
    def __init__(
        self,
        conn_str,
        username,
        password,
        bucket_name,
        scope_name="real_estate",
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
    scope_name="real_estate",  # match your setup
    collection_name="memory",  # match your setup
)


def save_user_preference(category: str, preference: str) -> dict:
    user_id = getattr(save_user_preference, "user_id", USER_ID)
    persistent_data.add(user_id=user_id, category=category, data=preference)
    return {
        "status": "success",
        "message": f"Preference saved in category '{category}'.",
    }


def retrieve_user_preferences(category: str) -> dict:
    user_id = getattr(retrieve_user_preferences, "user_id", USER_ID)
    results = persistent_data.search_by_category(user_id=user_id, category=category)
    return {"status": "success", "preferences": results, "count": len(results)}


def find_properties(location: str, budget: str) -> dict:
    user_id = getattr(save_user_preference, "user_id", USER_ID)
    property_prefs = persistent_data.search_by_category(user_id, "property_preferences")

    # Extract property preferences
    property_type = None
    preferred_features = []
    investment_type = "residential"

    for pref in property_prefs:
        if "investment" in pref.lower():
            investment_type = "investment"
        elif "rental" in pref.lower():
            investment_type = "rental"
        elif "apartment" in pref.lower() or "flat" in pref.lower():
            property_type = "apartment"
        elif "house" in pref.lower() or "villa" in pref.lower():
            property_type = "house"
        elif "pool" in pref.lower():
            preferred_features.append("pool")
        elif "garden" in pref.lower():
            preferred_features.append("garden")
        elif "garage" in pref.lower():
            preferred_features.append("garage")

    # Generate property recommendations based on preferences
    properties = []
    for _ in range(3):  # Generate 3 property suggestions
        property_type = property_type or random.choice(["apartment", "house"])
        
        property_data = {
            "type": property_type,
            "location": location,
            "price": f"{random.randint(int(budget.replace('EUR', '').strip()), int(budget.replace('EUR', '').strip()) + 100000)} EUR",
            "area": f"{random.randint(80, 200)} m²",
            "rooms": random.randint(2, 5),
            "bathrooms": random.randint(1, 3),
            "features": [f for f in preferred_features if random.random() > 0.3],
            "investment_type": investment_type,
            "notes": "",
        }

        # Add market analysis notes
        if investment_type == "investment":
            property_data["notes"] += f"Estimated rental yield: {random.randint(4, 7)}%"
        elif investment_type == "rental":
            property_data["notes"] += f"Current market rent: {random.randint(500, 1500)} EUR/month"

        properties.append(property_data)

    print(
        f"INFO: Generated {len(properties)} property suggestions for location: {location}"
    )

    return {
        "status": "success",
        "properties": properties,
        "recommendation": (
            f"Based on your preferences and budget of {budget}, we recommend focusing on {investment_type} properties."
            if investment_type
            else "Please specify your investment preferences (residential, investment, or rental) for better recommendations."
        )
    }


real_estate_advisor = Agent(
    name="Real Estate Advisor",
    model="gemini-2.5-flash",
    description="""
            Take in an email from a client and analyze their real estate needs. Provide thorough market research and expert advice
            tailored to the Portuguese property market. If no useful research can be found, reply with 'NO USEFUL RESEARCH FOUND'
            otherwise provide valuable insights and property recommendations.
            """,
    instruction="""
You are an expert Real Estate Advisor specializing in the Portuguese property market. Your role is to:
1. Understand client needs and preferences through email communication
2. Use `retrieve_user_preferences` with category 'property_preferences' to recall client history
3. Call `find_properties` with location and budget parameters to suggest suitable properties
4. Provide market analysis and negotiation support based on current market conditions
5. If no preferences exist, guide the client to save their preferences using `save_user_preference`

Key Expertise:
- Portuguese property market trends and values
- Property investment analysis
- Negotiation strategies
- Market research and analytics
- Client communication and relationship management
""",
    tools=[save_user_preference, retrieve_user_preferences, find_properties],)
)


session_service = InMemorySessionService()
APP_NAME = "real_estate_advisor_app"
SESSION_ID = "session_001"

runner = Runner(
    agent=travel_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def call_agent_async(query: str, user_id: str, session_id: str):
    print(f"\n>>> User ({user_id}): {query}")
    content = types.Content(role="user", parts=[types.Part(text=query)])
    setattr(save_user_preference, "user_id", user_id)
    setattr(retrieve_user_preferences, "user_id", user_id)

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_response = event.content.parts[0].text
            print(f"<<< Assistant: {final_response}")
            return final_response

    return "No response received."


async def interactive_chat():
    print("--- Starting Interactive Travel Assistant ---")
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
