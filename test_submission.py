import os
import json
from datetime import datetime
from bson import ObjectId
from app import create_block, sha256

# Dummy data for testing
feedback_id = ObjectId()
created_at = datetime.utcnow().isoformat()
user_username = "test_user"
user_hash = sha256(user_username + os.getenv("USER_SALT", "some_fixed_random_salt"))

fb_for_chain = {
    "id": str(feedback_id),
    "target_name": "target_1",
    "category": "General Feedback",
    "description": "Test feedback",
    "priority": "Low",
    "created_at": created_at,
    "user_hash": user_hash,
    "organization_id": "ORG-001",
    "ratings": {
        "indicator_1": 5,
        "indicator_2": 5,
        "indicator_3": 5,
        "indicator_4": 5,
    },
    "average_rating": 5.0,
}

print(f"Attempting test submission for ID: {feedback_id}")
success = create_block(
    feedback_id,
    fb_for_chain,
    "encrypted_user",
    "encrypted_desc",
    target_name="target_1",
    category="General Feedback",
    priority="Low",
    rating1=5,
    rating2=5,
    rating3=5,
    rating4=5,
    average_rating=5.0
)

if success:
    print("Test submission SUCCESSFUL")
else:
    print("Test submission FAILED")
