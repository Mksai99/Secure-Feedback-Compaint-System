from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['feedback_platform_db']
print(f"Collections: {db.list_collection_names()}")
