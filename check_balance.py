from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()
RPC_URL = os.getenv("RPC_URL")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
print("connected", w3.is_connected())
if w3.is_connected():
    print("chain id", w3.eth.chain_id)
    balance = w3.eth.get_balance(ACCOUNT_ADDRESS)
    print("balance (wei)", balance)
    print("balance (ether)", w3.from_wei(balance, 'ether'))
else:
    print("could not connect to blockchain")
