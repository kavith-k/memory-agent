from datetime import datetime
import random
from typing import Dict, List, Optional
import os

from memory import CouchbaseMemory

MODEL = "gemini-2.5-flash"

# Initialize memory system
persistent_data = CouchbaseMemory(
    conn_str=os.getenv("COUCHBASE_CONN_STR"),
    username=os.getenv("COUCHBASE_USERNAME"),
    password=os.getenv("COUCHBASE_PASSWORD"),
    bucket_name=os.getenv("COUCHBASE_BUCKET"),
    scope_name="real_estate",
    collection_name="memory",
)

USER_ID = "RealEstateClient"


def save_user_preference(category: str, preference: str) -> Dict:
    """
    Save user preferences to the memory system.
    
    Args:
        category (str): Category for the preference (e.g., 'property_preferences')
        preference (str): The preference to save
        
    Returns:
        Dict: Status message
    """
    user_id = getattr(save_user_preference, "user_id", USER_ID)
    persistent_data.add(user_id=user_id, category=category, data=preference)
    return {
        "status": "success",
        "message": f"Preference saved in category '{category}'.",
    }


def retrieve_user_preferences(category: str) -> Dict:
    """
    Retrieve user preferences from the memory system.
    
    Args:
        category (str): Category to retrieve preferences from
        
    Returns:
        Dict: Preferences and count
    """
    user_id = getattr(retrieve_user_preferences, "user_id", USER_ID)
    results = persistent_data.search_by_category(user_id=user_id, category=category)
    return {"status": "success", "preferences": results, "count": len(results)}


def find_properties(location: str, budget: str) -> Dict:
    """
    Find suitable properties based on location and budget.
    
    Args:
        location (str): Location to search in
        budget (str): Budget in EUR
        
    Returns:
        Dict: Property recommendations and analysis
    """
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

    # Generate property recommendations
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




# Initialize email storage
email_data = CouchbaseMemory(
    conn_str=os.getenv("COUCHBASE_CONN_STR"),
    username=os.getenv("COUCHBASE_USERNAME"),
    password=os.getenv("COUCHBASE_PASSWORD"),
    bucket_name=os.getenv("COUCHBASE_BUCKET"),
    scope_name="emails",
    collection_name="messages"
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




def get_email_by_id(email_id: str) -> dict:
    """
    Retrieve a specific email by its ID.
    
    Args:
        email_id (str): ID of the email to retrieve
        
    Returns:
        Dict: Email data or error message
    """
    try:
        result = email_data.get(email_id)
        return {
            "status": "success",
            "email": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
