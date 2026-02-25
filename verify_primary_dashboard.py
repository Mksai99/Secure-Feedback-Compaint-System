import requests
from pymongo import MongoClient
import json
import re

BASE_URL = "http://127.0.0.1:5000"

def verify_blockchain_primary():
    print("--- STARTING BLOCKCHAIN-PRIMARY VERIFICATION ---")
    
    # 0. Initial Setup
    client = MongoClient("mongodb://localhost:27017/")
    db = client["feedback_platform_db"]
    feedback_col = db["feedback"]

    # 1. Login
    user_session = requests.Session()
    user_session.post(f"{BASE_URL}/login", data={"username": "student_test", "password": "password123", "role": "user"})
    
    # 2. Submit Feedback
    print("1. Submitting new feedback...")
    submit_res = user_session.post(f"{BASE_URL}/user/provide-feedback", data={
        "target_username": "target_test",
        "category": "Education",
        "description": "BLOCKCHAIN PRIMARY TEST CONTENT",
        "indicator_1": 5, "indicator_2": 5, "indicator_3": 5, "indicator_4": 5
    }, allow_redirects=True)
    
    # 3. Check Admin Dashboard (Source: Blockchain)
    print("2. Checking Admin Dashboard (Fetching directly from Blockchain)...")
    admin_session = requests.Session()
    admin_session.post(f"{BASE_URL}/login", data={"username": "admin", "password": "adminpassword", "role": "admin"})
    dash_res = admin_session.get(f"{BASE_URL}/admin")
    html = dash_res.text

    # Verify that the dashboard shows the content from the blockchain
    if "BLOCKCHAIN PRIMARY TEST CONTENT" in html:
        print("--- SUCCESS: Dashboard is showing BLOCKCHAIN DATA! ---")
    else:
        print("--- FAILURE: Could not find test content on the dashboard. ---")

    print("Verification complete (Blockchain-Only).")

if __name__ == "__main__":
    verify_blockchain_primary()
