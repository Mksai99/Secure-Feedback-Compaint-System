from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['feedback_platform_db']

collections = ["users", "targets", "admins", "authorities"]
for coll_name in collections:
    print(f"\n=== {coll_name.upper()} COLLECTION ===")
    docs = list(db[coll_name].find())
    for doc in docs:
        role = doc.get("role", "NO ROLE")
        username = doc.get("username", "NO USERNAME")
        print(f"User: {username} | Role: {role}")
