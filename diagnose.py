from pymongo import MongoClient
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

def check_db():
    print("--- MongoDB Status ---")
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()
        print("MongoDB: Connected")
        db = client["feedback_platform_db"]
        print(f"Collections: {db.list_collection_names()}")
        
        for col_name in ["users", "targets", "admins", "authorities"]:
            col = db[col_name]
            count = col.count_documents({})
            print(f"Collection '{col_name}': {count} documents")
            for doc in col.find():
                print(f"  - {doc.get('username')} (Verified: {doc.get('is_verified')}, Token: {doc.get('verification_token')})")
                
    except Exception as e:
        print(f"MongoDB: Error - {e}")

def check_blockchain():
    print("\n--- Blockchain Status ---")
    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if w3.is_connected():
        print(f"Blockchain (Ganache): Connected to {rpc_url}")
        print(f"Network ID: {w3.eth.chain_id}")
        print(f"Accounts: {w3.eth.accounts[:2]}")
    else:
        print(f"Blockchain (Ganache): DISCONNECTED from {rpc_url}")

if __name__ == "__main__":
    check_db()
    check_blockchain()
