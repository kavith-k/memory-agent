from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from memory import CouchbaseMemory
from tools import save_user_preference, retrieve_user_preferences, find_properties

# Initialize session service and runner
session_service = InMemorySessionService()

# Create the Real Estate Advisor agent
real_estate_advisor = Agent(
    name="RealEstateAdvisor",
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
    tools=[save_user_preference, retrieve_user_preferences, find_properties],
)

# Create runner instance
runner = Runner(
    agent=real_estate_advisor,
    app_name="real_estate_advisor_app",
    session_service=session_service,
)

async def call_agent_async(query: str, user_id: str, session_id: str):
    print(f"\n>>> User ({user_id}): {query}")
    content = types.Content(role="user", parts=[types.Part(text=query)])
    setattr(save_user_preference, "user_id", user_id)
    setattr(retrieve_user_preferences, "user_id", user_id)

    async for event in runner.run_async(
        content=content,
        session_id=session_id,
        user_id=user_id,
    ):
        if event.type == "message":
            print(f"\n<<< Agent: {event.content.parts[0].text}")
        elif event.type == "error":
            print(f"\n!!! Error: {event.content.parts[0].text}")

async def create_session():
    await session_service.create_session(
        app_name="real_estate_advisor_app", user_id=USER_ID, session_id=SESSION_ID
    )
