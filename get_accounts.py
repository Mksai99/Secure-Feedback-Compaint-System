from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

if w3.is_connected():
    accounts = w3.eth.accounts
    print(f"ACCOUNTS_FOUND: {len(accounts)}")
    for i, acc in enumerate(accounts):
        print(f"Account {i}: {acc}")
else:
    print("FAILED_TO_CONNECT")
