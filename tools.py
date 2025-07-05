from datetime import datetime
import random
from typing import Dict, List
import os

from memory import CouchbaseMemory

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


def save_email(message: Dict) -> Dict:
    """
    Save an email message to the database.
    
    Args:
        message (Dict): Email message with required fields: date, from, to, subject, body
        
    Returns:
        Dict: Status message
    """
    required_fields = ['date', 'from', 'to', 'subject', 'body']
    if not all(field in message for field in required_fields):
        return {
            "status": "error",
            "message": "Missing required fields: " + ", ".join(required_fields)
        }
    
    # Generate a unique ID for the email
    email_id = f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    message['id'] = email_id
    
    # Save to database
    email_data.add(user_id="system", category="email", data=message)
    
    return {
        "status": "success",
        "message": f"Email saved with ID: {email_id}",
        "email_id": email_id
    }


def retrieve_emails(filters: Optional[Dict] = None) -> Dict:
    """
    Retrieve emails from the database based on optional filters.
    
    Args:
        filters (Dict, optional): Filters to apply to the search. Can include:
            - date: specific date or date range
            - from: sender email
            - to: recipient email
            - subject: subject contains
    
    Returns:
        Dict: List of matching emails and total count
    """
    query = "SELECT META().id, m.* FROM `messages` m WHERE category = 'email'"
    params = {}
    
    if filters:
        conditions = []
        if 'date' in filters:
            date = filters['date']
            if isinstance(date, tuple):  # Date range
                conditions.append("date BETWEEN $start_date AND $end_date")
                params['start_date'] = date[0]
                params['end_date'] = date[1]
            else:  # Specific date
                conditions.append("date = $date")
                params['date'] = date
        
        if 'from' in filters:
            conditions.append("`from` = $from")
            params['from'] = filters['from']
        
        if 'to' in filters:
            conditions.append("`to` = $to")
            params['to'] = filters['to']
        
        if 'subject' in filters:
            conditions.append("subject LIKE $subject")
            params['subject'] = f"%{filters['subject']}%"
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
    
    query += " ORDER BY date DESC LIMIT 100"
    
    try:
        results = email_data.query(query, params)
        return {
            "status": "success",
            "emails": results,
            "count": len(results)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def get_email_by_id(email_id: str) -> Dict:
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
