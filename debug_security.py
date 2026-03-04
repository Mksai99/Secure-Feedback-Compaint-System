from pymongo import MongoClient
import hashlib

client = MongoClient("mongodb://localhost:27017/")
db = client["feedback_platform_db"]

def inspect():
    print("--- Users ---")
    for u in db.users.find({"username": {"$regex": "security"}}):
        print(f"User: {u['username']}, Token: {u.get('verification_token')}, Verified: {u.get('is_verified')}")
    print("\n--- Targets ---")
    for t in db.targets.find({"username": {"$regex": "security"}}):
        print(f"Target: {t['username']}, Token: {t.get('verification_token')}, Verified: {t.get('is_verified')}")

inspect()
