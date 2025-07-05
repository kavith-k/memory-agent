from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# from memory import CouchbaseMemory
from tools import store_email, retrieve_emails, get_email_by_id, MODEL

# Create the Email Agent
e_mail_agent = Agent(
    name="EmailAssistant",
    model=MODEL,
    description="""
        An intelligent email assistant that can manage and analyze email communications.
        Can store, retrieve, and analyze emails with fields: date, from, to, subject, body.
        Also supports chat-like interactions.
    """,
    instruction="""
You are an Email Assistant that can:
1. Store emails/chats with proper metadata (date, sender, recipient, subject, body)
2. Retrieve emails based on various filters (date, sender, recipient, subject)
3. Analyze email content and provide insights
4. Handle both email and chat-like communications

Key Features:
- Email storage and retrieval
- Advanced search capabilities
- Content analysis and summarization
- Chat message handling
- Integration with real estate advisor
    """,
    tools=[store_email, retrieve_emails, get_email_by_id]
)
