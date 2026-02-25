import json
import os
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:7545") # Default Ganache UI port
CHAIN_ID = int(os.getenv("CHAIN_ID", 5777))
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")

def deploy():
    if not PRIVATE_KEY or not ACCOUNT_ADDRESS:
        print("Error: PRIVATE_KEY and ACCOUNT_ADDRESS must be set in .env")
        return

    # 1. Connect to Web3
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print(f"Error: Could not connect to RPC at {RPC_URL}")
        return
    print(f"Connected to blockchain at {RPC_URL}")

    # 2. Compile Solidity
    print("Compiling FeedbackRegistry.sol...")
    install_solc("0.8.0")
    with open("contracts/FeedbackRegistry.sol", "r") as f:
        feedback_registry_file = f.read()

    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"FeedbackRegistry.sol": {"content": feedback_registry_file}},
            "settings": {
                "optimizer": {
                    "enabled": True,
                    "runs": 200
                },
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            },
        },
        solc_version="0.8.0",
    )

    # 3. Extract ABI and Bytecode
    bytecode = compiled_sol["contracts"]["FeedbackRegistry.sol"]["FeedbackRegistry"]["evm"]["bytecode"]["object"]
    abi = compiled_sol["contracts"]["FeedbackRegistry.sol"]["FeedbackRegistry"]["abi"]

    # 4. Create Contract Instance
    FeedbackRegistry = w3.eth.contract(abi=abi, bytecode=bytecode)

    # 5. Check balance before building transaction
    balance_wei = w3.eth.get_balance(ACCOUNT_ADDRESS)
    balance_eth = w3.from_wei(balance_wei, "ether")
    print(f"Account {ACCOUNT_ADDRESS} balance: {balance_eth} ETH")
    if balance_wei == 0:
        print(
            "Error: account has no ETH. "
            "Use a funded Ganache account or transfer funds before deploying."
        )
        return

    # 6. Build Transaction
    print("Deploying contract...")
    nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)
    transaction = FeedbackRegistry.constructor().build_transaction(
        {
            "chainId": CHAIN_ID,
            "from": ACCOUNT_ADDRESS,
            "nonce": nonce,
            "gasPrice": w3.eth.gas_price,
        }
    )

    # 6. Sign and Send Transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    # 7. Wait for Receipt
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Contract deployed at: {tx_receipt.contractAddress}")

    # 8. Save Artifacts for app.py
    artifacts = {
        "address": tx_receipt.contractAddress,
        "abi": abi
    }
    with open("contract_artifacts.json", "w") as f:
        json.dump(artifacts, f, indent=4)
    print("Artifacts saved to contract_artifacts.json")

if __name__ == "__main__":
    deploy()
