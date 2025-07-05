import os
import asyncio
from dotenv import load_dotenv

from .real_estate_agent import real_estate_advisor, call_agent_async, create_session

# Load environment variables from .env file
load_dotenv()

USER_ID = "RealEstateClient"

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
