from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# from memory import CouchbaseMemory
from tools import save_email, retrieve_emails, get_email_by_id

# Create the Email Agent
e_mail_agent = Agent(
    name="EmailAssistant",
    model="gemini-2.5-flash",
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
    tools=[
        {
            "name": "save_email",
            "description": "Save an email or chat message to the database",
            "function": save_email,
            "type": "function"
        },
        {
            "name": "retrieve_emails",
            "description": "Retrieve emails based on filters",
            "function": retrieve_emails,
            "type": "function"
        },
        {
            "name": "get_email_by_id",
            "description": "Retrieve a specific email by its ID",
            "function": get_email_by_id,
            "type": "function"
        }
    ]
)
