from web3 import Web3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def check_blockchain():
    RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not os.path.exists("contract_artifacts.json"):
        print("contract_artifacts.json not found")
        return

    with open("contract_artifacts.json", "r") as f:
        artifacts = json.load(f)
    
    contract = w3.eth.contract(address=artifacts["address"], abi=artifacts["abi"])
    
    count = contract.functions.totalFeedbackCount().call()
    print(f"Total Feedback Count on-chain: {count}")
    
    if count > 0:
        ids = contract.functions.getAllFeedbackIds().call()
        print(f"All IDs: {ids}")
        for fid in ids:
            record = contract.functions.getFeedbackRecord(fid).call()
            print(f"ID: {fid} | Target: {record[3]} | Category: {record[4]} | Priority: {record[5]} | Exists: {record[8]}")

if __name__ == "__main__":
    check_blockchain()
