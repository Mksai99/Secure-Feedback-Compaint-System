from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['feedback_platform_db']

collections = ["users", "targets", "admins", "authorities"]
for coll_name in collections:
    print(f"\n--- Collection: {coll_name} ---")
    docs = list(db[coll_name].find())
    if not docs:
        print("Empty")
    for doc in docs:
        print(doc)
