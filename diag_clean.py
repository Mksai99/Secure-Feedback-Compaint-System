from pymongo import MongoClient
import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

def run_diag():
    print("--- DIAGNOSTIC START ---")
    
    # DB Check
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        db = client["feedback_platform_db"]
        print("MongoDB: Connected")
        
        for col_name in ["users", "targets", "admins", "authorities"]:
            print(f"\nCollection: {col_name}")
            col = db[col_name]
            for doc in col.find():
                # Clean up doc for printing
                clean_doc = {k: str(v) for k, v in doc.items() if k != "_id"}
                print(f"  {clean_doc}")
                
    except Exception as e:
        print(f"MongoDB Error: {e}")

    # Blockchain Check
    try:
        rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if w3.is_connected():
            print(f"\nBlockchain: Connected to {rpc_url}")
            print(f"  Chain ID: {w3.eth.chain_id}")
        else:
            print(f"\nBlockchain: DISCONNECTED from {rpc_url}")
    except Exception as e:
        print(f"Blockchain Error: {e}")

    print("\n--- DIAGNOSTIC END ---")

if __name__ == "__main__":
    run_diag()
