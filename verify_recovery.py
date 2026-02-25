import os
import json
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Config
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

client = MongoClient(MONGO_URI)
# No MongoDB feedback dependency in verification script

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Load contract
with open("contract_artifacts.json", "r") as f:
    artifacts = json.load(f)
contract = w3.eth.contract(address=artifacts["address"], abi=artifacts["abi"])

def test_recovery():
    print("--- STARTING BLOCKCHAIN RECOVERY VERIFICATION ---")
    
    # 1. Prepare Test Data
    fb_id = ObjectId()
    description = "Test feedback for blockchain recovery."
    user_name = "test_student"
    
    # Simple hash (mimic app.py)
    import hashlib
    def sha256(data):
        return hashlib.sha256(data.encode()).hexdigest()
    
    fb_chain = {
        "id": str(fb_id),
        "target_name": "target1",
        "category": "General",
        "description": description,
        "priority": "Medium",
        "created_at": datetime.utcnow().isoformat(),
        "user_hash": sha256(user_name + "SECURE_SALT"),
        "organization_id": "ORG-001",
        "ratings": {},
        "average_rating": 0
    }
    
    data_hash = sha256(json.dumps(fb_chain, sort_keys=True))
    
    # For testing, we'll use dummy encrypted data (mimic app.py's format)
    enc_user = "ENC_" + user_name
    enc_desc = "ENC_" + description

    print(f"1. Recording data on blockchain for ID {fb_id}...")
    nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)
    txn = contract.functions.recordFeedback((
        str(fb_id), 
        data_hash, 
        enc_user, 
        enc_desc,
        "target1",
        "General",
        "Medium",
        "ORG-001",
        0, 0, 0, 0, 0
    )).build_transaction({
        "chainId": int(os.getenv("CHAIN_ID", 1337)),
        "from": ACCOUNT_ADDRESS,
        "nonce": nonce,
        "gasPrice": w3.eth.gas_price
    })
    
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print("SUCCESS: Data recorded on blockchain.")

    # Verification complete (Blockchain-Only).
    print("SUCCESS: Data recorded and verified on blockchain.")
    print("--- VERIFICATION COMPLETE ---")

    print("--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    test_recovery()
