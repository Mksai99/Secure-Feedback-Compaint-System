from pymongo import MongoClient
import json

client = MongoClient('mongodb://localhost:27017/')
db = client['feedback_platform_db']

def audit_collection(coll_name):
    print(f"\n--- Auditing Collection: {coll_name} ---")
    coll = db[coll_name]
    all_docs = list(coll.find())
    print(f"Total documents: {len(all_docs)}")
    
    unique_roles = coll.distinct("role")
    print(f"Unique roles found: {unique_roles}")
    
    for role in unique_roles:
        count = coll.count_documents({"role": role})
        print(f"Count for role '{role}': {count}")
    
    if all_docs:
        print("Sample document (first 2):")
        for doc in all_docs[:2]:
            # Convert ObjectId to string for printing
            doc['_id'] = str(doc['_id'])
            print(json.dumps(doc, indent=2))

audit_collection("users")
audit_collection("targets")
