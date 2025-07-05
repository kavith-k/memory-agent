from datetime import datetime
import random
from typing import Dict, List

from .memory import CouchbaseMemory

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
