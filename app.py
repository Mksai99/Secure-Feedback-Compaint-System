from flask import Flask, render_template, request, redirect, session, url_for, flash
import json
import logging
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import hashlib
from cryptography.fernet import Fernet
import os
from web3 import Web3
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import time
from flask_mail import Mail, Message
import secrets
import requests

# Configure Logging
logging.basicConfig(filename='app_error.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s: %(message)s')

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "any_random_long_secret_here")

# ---------- Supabase REST API Config ----------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Warning: Missing Supabase credentials in .env")
# ---------- Mail Configuration ----------
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
mail = Mail(app)

BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000')


# secret salt for user anonymity (stored on-chain)
USER_SALT = os.getenv("USER_SALT", "some_fixed_random_salt")

# ---------- Real Blockchain (Web3) Setup ----------
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = None

def load_contract():
    global contract
    try:
        if os.path.exists("contract_artifacts.json"):
            with open("contract_artifacts.json", "r") as f:
                artifacts = json.load(f)
            contract = w3.eth.contract(address=artifacts["address"], abi=artifacts["abi"])
            print(f"Connected to smart contract at {artifacts['address']}")
        else:
            print("Warning: contract_artifacts.json not found. Deploy the contract first.")
    except Exception as e:
        print(f"Error loading contract: {e}")

load_contract()

# ---------- Encryption Setup ----------
KEY_FILE = "secret.key"

def load_key():
    """Load the previously generated key if exists, else generate new."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key

metrics_key = load_key()
cipher_suite = Fernet(metrics_key)

def encrypt_data(data: str) -> str:
    """Encrypts a string and returns a string token."""
    if not data:
        return ""
    # Fernet encrypt expects bytes, returns bytes
    token = cipher_suite.encrypt(data.encode("utf-8"))
    return token.decode("utf-8")

def decrypt_data(token: str) -> str:
    """Decrypts a string token and returns original string."""
    if not token:
        return ""
    # Fernet decrypt expects bytes
    data_bytes = cipher_suite.decrypt(token.encode("utf-8"))
    return data_bytes.decode("utf-8")


# ---------- Helpers ----------
def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()




# get_last_block removed (redundant)


def create_block(feedback_id: ObjectId, feedback_data: dict, encrypted_user: str = "", encrypted_desc: str = "",
                 target_name: str = "", category: str = "", priority: str = "", organization_id: str = "ORG-001",
                 rating1: int = 0, rating2: int = 0, rating3: int = 0, rating4: int = 0, average_rating: float = 0.0):
    """
    Records ALL feedback data on-chain — blockchain is the single source of truth.
    Ratings are stored as uint8 (0-5), averageRating as uint256 * 100 (e.g. 4.25 → 425).
    """
    print(f"DEBUG: create_block called for fb_id: {feedback_id}")
    if not contract or not ACCOUNT_ADDRESS or not PRIVATE_KEY:
        print(f"DEBUG: Blockchain config missing - Contract: {bool(contract)}, Account: {ACCOUNT_ADDRESS}, Key: {'SET' if PRIVATE_KEY else 'MISSING'}")
        return

    try:
        data_json = json.dumps(feedback_data, sort_keys=True)
        data_hash = sha256(data_json)
        fb_id_str = str(feedback_id)
        # Convert average_rating to integer * 100 for on-chain storage
        avg_rating_int = int(round(average_rating * 100))

        print(f"DEBUG: Preparing transaction for {fb_id_str} with ratings {rating1},{rating2},{rating3},{rating4} avg={avg_rating_int}...")
        nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)
        # Call recordFeedback with all fields — blockchain is the authoritative store
        txn = contract.functions.recordFeedback((
            fb_id_str,
            data_hash,
            encrypted_user,
            encrypted_desc,
            target_name,
            category,
            priority,
            organization_id,
            rating1,
            rating2,
            rating3,
            rating4,
            avg_rating_int
        )).build_transaction({
            "chainId": int(os.getenv("CHAIN_ID", 1337)),
            "from": ACCOUNT_ADDRESS,
            "nonce": nonce,
            "gasPrice": w3.eth.gas_price
        })

        print(f"DEBUG: Signing transaction...")
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        print(f"DEBUG: Sending transaction...")
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"DEBUG: Waiting for receipt...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # No MongoDB mirroring - Blockchain is the only store
        print(f"SUCCESS: Feedback {fb_id_str} recorded on-chain with ratings. TX: {tx_receipt.transactionHash.hex()}")
        return True
    except Exception as e:
        error_msg = f"CRITICAL BLOCKCHAIN ERROR in create_block for {feedback_id}: {e}"
        print(error_msg)
        logging.error(error_msg, exc_info=True)
        return False




# verify_chain removed: MongoDB no longer stores feedback data.




def current_user():
    """Returns the current user details securely stored in the session by verifying with Supabase."""
    access_token = request.cookies.get("sb-access-token")
    if not access_token or not SUPABASE_URL:
        return None
    
    try:
        # Validate the token securely with Supabase REST API
        url = f"{SUPABASE_URL}/auth/v1/user"
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            # Extract role and username mapped during creation
            app_meta = user_data.get("app_metadata", {})
            user_meta = user_data.get("user_metadata", {})
            
            role = user_meta.get("role", "user")
            username = user_meta.get("username", user_data.get("email"))
            return {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "username": username,
                "role": role
            }
    except Exception as e:
        print(f"Session validation failed: {str(e)}")
        return None
    return None

def login_required(role=None):
    """Decorator to enforce Supabase Auth session validation and role checks."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return redirect(url_for("login"))
            
            # Pass the user data to the session so templates can render username/roles effortlessly
            session["username"] = user["username"]
            session["role"] = user["role"]

            if role and user["role"] != role:
                return "Unauthorized Access", 403
            
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator


# ---------- Routes ----------

@app.route("/")
def home():
    return render_template(
        "home.html",
        title="Secure Anonymous Feedback Platform",
        heading="Privacy-Preserving Feedback System",
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            # Supabase REST Authentication
            url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
            headers = {
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json"
            }
            data = {
                "email": email,
                "password": password
            }
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                raise Exception(response.json().get("error_description", "Invalid login"))
            
            auth_response = response.json()
            user = auth_response.get("user", {})
            user_meta = user.get("user_metadata", {})
            role = user_meta.get("role", "user")
            
            # Use app.make_response to set secure cookies
            if role == "user":
                resp = app.make_response(redirect(url_for("user_submit_feedback")))
            elif role == "target":
                resp = app.make_response(redirect(url_for("target_view_feedback")))
            elif role == "authority":
                resp = app.make_response(redirect(url_for("authority_dashboard")))
            else:
                resp = app.make_response(redirect(url_for("admin_dashboard")))
            
            # Set the JWT securely in HTTP-only cookies
            resp.set_cookie("sb-access-token", auth_response.get("access_token"), httponly=True, secure=True)
            resp.set_cookie("sb-refresh-token", auth_response.get("refresh_token"), httponly=True, secure=True)
            
            return resp
            
        except Exception as e:
            print(f"Supabase Login Error: {e}")
            return render_template(
                "login.html",
                error="Invalid credentials. Please verify your email and password.",
                title="Login",
                heading="Login",
            )

    return render_template("login.html", error=None, title="Login", heading="Login")


@app.route("/verify-email/<token>", methods=["GET", "POST"])
def verify_email(token):
    # Clear any existing session to prevent conflicting states (e.g. Admin sees their sidebar on verification page)
    session.clear()
    
    role = request.args.get("role", "user")
    if role == "user":
        col = users_col
    elif role == "target":
        col = targets_col
    else:
        return "Invalid role", 400

    hashed_token = sha256(token)
    user = col.find_one({"verification_token": hashed_token})
    if not user:
        return "Invalid or expired verification token.", 404

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            return render_template("verify_email.html", token=token, role=role, error="Passwords do not match")

        hashed_pwd = generate_password_hash(password)
        col.update_one(
            {"_id": user["_id"]},
            {"$set": {"password": hashed_pwd, "is_verified": True}, "$unset": {"verification_token": ""}}
        )
        return render_template("verify_success.html", title="Account Activated")

    return render_template("verify_email.html", token=token, role=role, username=user["username"])


@app.route("/logout")
def logout():
    session.clear()
    resp = app.make_response(redirect(url_for("login")))
    resp.delete_cookie("sb-access-token")
    resp.delete_cookie("sb-refresh-token")
    try:
        access_token = request.cookies.get("sb-access-token")
        if access_token and SUPABASE_URL:
             url = f"{SUPABASE_URL}/auth/v1/logout"
             headers = {
                 "apikey": SUPABASE_ANON_KEY,
                 "Authorization": f"Bearer {access_token}"
             }
             requests.post(url, headers=headers)
    except Exception:
        pass
    return resp


@app.route("/update-password", methods=["GET", "POST"])
def update_password():
    """Handles setting/updating a password after clicking an email invite link."""
    # The GET request just renders the form which includes JS to parse the URL hash
    if request.method == "GET":
        return render_template("update_password.html", title="Set Password")
        
    # POST request actually does the update
    new_password = request.form.get("password")
    access_token = request.form.get("access_token")
    
    if not new_password or not access_token:
        flash("Missing password or invalid token.", "danger")
        return redirect(url_for("update_password"))
        
    try:
        url = f"{SUPABASE_URL}/auth/v1/user"
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "password": new_password
        }
        response = requests.put(url, headers=headers, json=data)
        
        if response.status_code == 200:
            flash("Password set successfully! You can now log in.", "success")
            return redirect(url_for("login"))
        else:
            flash(f"Error updating password: {response.json().get('error_description', 'Unknown error')}", "danger")
            return redirect(url_for("update_password"))
            
    except Exception as e:
        flash("Connection error while setting password.", "danger")
        return redirect(url_for("update_password"))

@app.route("/jwt-status")
@login_required()
def jwt_status():
    token = session.get("jwt_token")
    if not token:
        return {"status": "error", "message": "No JWT token found in session."}
    
    payload = verify_jwt_token(token)
    if not payload:
        return {"status": "error", "message": "Invalid or expired JWT token."}
    
    return {
        "status": "success",
        "token_preview": f"{token[:10]}...{token[-10:]}",
        "decoded_payload": payload,
        "is_secure": True
    }


# ----- User -----
@app.route("/user/provide-feedback", methods=["GET", "POST"])
@login_required(role="user")
def user_submit_feedback():
    if request.method == "POST":
        submission_type = request.form.get("submission_type", "feedback")
        target_name = request.form.get("target_username")
        description = request.form.get("description")
        
        # Default values
        category = "General Feedback"
        priority = "Low"
        rating_1 = 0
        rating_2 = 0
        rating_3 = 0
        rating_4 = 0

        if submission_type == "complaint":
            category = request.form.get("category", "Other")
            priority = request.form.get("priority", "Medium")
        else:
            # It's feedback
            rating_1 = int(request.form.get("rating_1", 0))
            rating_2 = int(request.form.get("rating_2", 0))
            rating_3 = int(request.form.get("rating_3", 0))
            rating_4 = int(request.form.get("rating_4", 0))

        print(f"DEBUG: {submission_type.upper()} submission received for {target_name}. Category: {category}")

        created_at = datetime.utcnow().isoformat()
        avg_rating = round((rating_1 + rating_2 + rating_3 + rating_4) / 4.0, 2) if submission_type == "feedback" else 0.0

        user_username = session["username"]
        # anonymized user id
        user_hash = sha256(user_username + USER_SALT)

        # Generate ID manually to ensure consistency between Blockchain and MongoDB
        feedback_id = ObjectId()

        # 1. Prepare Blockchain Data
        fb_for_chain = {
            "id": str(feedback_id),
            "target_name": target_name,
            "category": category,
            "description": description,
            "priority": priority,
            "created_at": created_at,
            "user_hash": user_hash,
            "organization_id": "ORG-001",
            "ratings": {
                "indicator_1": rating_1,
                "indicator_2": rating_2,
                "indicator_3": rating_3,
                "indicator_4": rating_4,
            },
            "average_rating": avg_rating,
        }

        encrypted_user = encrypt_data(user_username)
        encrypted_desc = encrypt_data(description)

        # 2. Blockchain Write (Single Source of Truth)
        # Attempt to record on blockchain first. If this fails, we do NOT save to MongoDB.
        print(f"DEBUG: Attempting Blockchain-First write for {feedback_id}")
        tx_success = create_block(
            feedback_id,
            fb_for_chain,
            encrypted_user,
            encrypted_desc,
            target_name=target_name,
            category=category,
            priority=priority,
            organization_id="ORG-001",
            rating1=rating_1,
            rating2=rating_2,
            rating3=rating_3,
            rating4=rating_4,
            average_rating=avg_rating
        )

        if tx_success:
            print(f"DEBUG: Feedback {feedback_id} recorded successfully on-chain.")
        else:
            print(f"CRITICAL: Blockchain write FAILED for {feedback_id}.")
            return "Error: Blockchain transaction failed. Feedback not submitted.", 500

        return redirect(url_for("user_submit_feedback"))

    # GET – show form with targets list
    target_list = []
    try:
        if SUPABASE_URL:
            url = f"{SUPABASE_URL}/auth/v1/admin/users"
            headers = {
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                users_data = response.json().get("users", [])
                for u in users_data:
                    user_meta = u.get("user_metadata", {})
                    if user_meta.get("role") == "target":
                        username = user_meta.get("username", u.get("email"))
                        target_list.append({"username": username})
    except Exception as e:
        print(f"Error loading targets for feedback dropdown: {str(e)}")
    return render_template(
        "submit_feedback.html",
        target_list=target_list,
        title="Submit Anonymous Feedback",
        heading="User Panel",
    )


# ----- Target -----
@app.route("/target/view-feedback")
@login_required(role="target")
def target_view_feedback():
    target_username = session["username"]
    feedback_list = []

    if not contract:
        return render_template(
            "view_feedback.html",
            feedback_list=[],
            title="Received Feedback",
            heading="Target Panel — Blockchain Not Connected"
        )

    try:
        # Blockchain is the only source of truth — no MongoDB reads
        on_chain_ids = contract.functions.getAllFeedbackIds().call()
        for fid in on_chain_ids:
            # getFeedbackCore: 0:dataHash 1:encUser 2:encDesc 3:targetName 4:category 5:priority 6:orgId
            # getFeedbackMeta: 0:r1 1:r2 2:r3 3:r4 4:avgRating 5:revealStatus 6:timestamp 7:exists
            core = contract.functions.getFeedbackCore(fid).call()
            meta = contract.functions.getFeedbackMeta(fid).call()
            if not meta[7]:  # exists
                continue
            if core[3] != target_username:
                continue

            try:
                dec_desc = decrypt_data(core[2])
            except Exception:
                dec_desc = "[DECRYPTION FAILED]"

            avg = meta[4] / 100.0 if meta[4] else 0.0
            created_at = datetime.fromtimestamp(meta[6]).isoformat() if meta[6] > 0 else "Unknown"

            feedback_list.append({
                "category": core[4],
                "description": dec_desc,
                "priority": core[5],
                "created_at": created_at,
                "avg": round(avg, 2),
                "ind1": meta[0],
                "ind2": meta[1],
                "ind3": meta[2],
                "ind4": meta[3],
            })

        feedback_list.sort(key=lambda x: x["created_at"], reverse=True)
    except Exception as e:
        print(f"TARGET DASHBOARD BLOCKCHAIN ERROR: {e}")

    return render_template(
        "view_feedback.html",
        feedback_list=feedback_list,
        title="Received Feedback",
        heading="Target Panel",
    )


# ----- Admin -----
@app.route("/admin")
@login_required(role="admin")
def admin_dashboard():
    target_list = []
    user_list = []
    
    # Safely fetch users from Supabase Admin REST API
    try:
        if SUPABASE_URL:
            url = f"{SUPABASE_URL}/auth/v1/admin/users"
            headers = {
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                users_data = response.json().get("users", [])
                for u in users_data:
                    user_meta = u.get("user_metadata", {})
                    role = user_meta.get("role")
                    username = user_meta.get("username", u.get("email"))
                    
                    # Format to match Jinja template expectations
                    user_record = {
                        "id": u.get("id"),
                        "username": username,
                        "email": u.get("email"),
                        "is_verified": bool(u.get("email_confirmed_at"))
                    }
                    
                    if role == "target":
                        target_list.append(user_record)
                    elif role == "user":
                        user_list.append(user_record)
    except Exception as e:
        print(f"Error loading users from Supabase: {str(e)}")
        flash("Could not load users from authentication service.", "danger")

    feedback_list = []
    compromised_ids = []
    chain_valid = True

    if not contract:
        return render_template("admin_dashboard.html", target_list=target_list, user_list=user_list, feedback_list=[], chain_valid=False, title="Admin Dashboard", heading="Chain Not Connected")

    try:
        # Blockchain is the ONLY source of truth — No MongoDB dependency
        on_chain_ids = contract.functions.getAllFeedbackIds().call()

        for fid in on_chain_ids:
            # getFeedbackCore: 0:dataHash 1:encUser 2:encDesc 3:targetName 4:category 5:priority 6:orgId
            core = contract.functions.getFeedbackCore(fid).call()
            # getFeedbackMeta: 0:r1 1:r2 2:r3 3:r4 4:avgRating 5:revealStatus 6:timestamp 7:exists
            meta = contract.functions.getFeedbackMeta(fid).call()
            
            if not meta[7]:  # exists
                continue

            try:
                dec_desc = decrypt_data(core[2])
            except Exception:
                dec_desc = "[DECRYPTION FAILED]"

            avg = meta[4] / 100.0 if meta[4] else 0.0
            created_at = datetime.fromtimestamp(meta[6]).isoformat() if meta[6] > 0 else "Unknown"

            fb_item = {
                "id": fid,
                "target_name": core[3],
                "category": core[4],
                "description": dec_desc,
                "priority": core[5],
                "created_at": created_at,
                "avg": round(avg, 2),
                "reveal_status": meta[5],
                "tx_hash": "BLOCKCHAIN-SOURCE",
                "status": "Verified"
            }
            feedback_list.append(fb_item)

        feedback_list.sort(key=lambda x: x['created_at'], reverse=True)
        chain_valid = True

    except Exception as e:
        print(f"DASHBOARD ERROR: {e}")
        chain_valid = False

    return render_template(
        "admin_dashboard.html",
        target_list=target_list,
        user_list=user_list,
        feedback_list=feedback_list,
        chain_valid=chain_valid,
        compromised_ids=[],
        title="Administrator Control Center",
        heading="Platform Administration",
    )


@app.route("/admin/add-target", methods=["POST"])
@login_required(role="admin")
def admin_add_target():
    username = request.form.get("username")
    email = request.form.get("email")
    if username and email:
        try:
            # Force the redirect back to the Flask app instead of the default port 3000
            url = f"{SUPABASE_URL}/auth/v1/invite?redirect_to=http://127.0.0.1:5000/update-password"
            headers = {
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "email": email,
                "data": {"role": "target", "username": username}
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                flash(f"Verification email sent to target: {username}", "success")
            else:
                error_msg = response.json().get("msg", response.json().get("error_description", response.text))
                if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
                    flash(f"Error: The email '{email}' is already registered to an existing account.", "danger")
                else:
                    flash(f"Error creating target: {error_msg}", "danger")
        except Exception as e:
            flash(f"Error creating target: {str(e)}", "danger")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/add-user", methods=["POST"])
@login_required(role="admin")
def admin_add_user():
    username = request.form.get("username")
    email = request.form.get("email")
    if username and email:
        try:
            url = f"{SUPABASE_URL}/auth/v1/invite?redirect_to=http://127.0.0.1:5000/update-password"
            headers = {
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "email": email,
                "data": {"role": "user", "username": username}
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                flash(f"Verification email sent to user: {username}", "success")
            else:
                error_msg = response.json().get("msg", response.json().get("error_description", response.text))
                if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
                    flash(f"Error: The email '{email}' is already registered to an existing account.", "danger")
                else:
                    flash(f"Error creating user: {error_msg}", "danger")
        except Exception as e:
            flash(f"Error creating user: {str(e)}", "danger")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete-user/<user_id>", methods=["POST"])
@login_required(role="admin")
def admin_delete_user(user_id):
    try:
        url = f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}"
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
        }
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            flash("User deleted successfully.", "success")
        else:
            flash(f"Failed to delete user: {response.text}", "danger")
    except Exception as e:
        flash(f"Failed to delete user: {e}", "danger")
    return redirect(url_for("admin_dashboard"))


# Admin Deletion/Recovery/Sync removed: System is now Blockchain-Only and immutable.

@app.route("/debug/blockchain")
def debug_blockchain():
    if not contract:
        return {"status": "error", "message": "No contract loaded"}
    try:
        count = contract.functions.totalFeedbackCount().call()
        ids = contract.functions.getAllFeedbackIds().call()
        return {
            "address": contract.address,
            "count": count,
            "ids": ids,
            "account": ACCOUNT_ADDRESS,
            "is_connected": w3.is_connected()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ----- Authority -----
@app.route("/authority")
@login_required(role="authority")
def authority_dashboard():
    feedback_list = []

    if not contract:
        return render_template(
            "authority_dashboard.html",
            feedback_list=[],
            title="Authority Oversight",
            heading="Authority Panel — Blockchain Not Connected"
        )

    try:
        # Blockchain is the ONLY source of truth — no MongoDB feedback reads
        on_chain_ids = contract.functions.getAllFeedbackIds().call()
        for fid in on_chain_ids:
            # getFeedbackCore: 0:dataHash 1:encUser 2:encDesc 3:targetName 4:category 5:priority 6:orgId
            # getFeedbackMeta: 0:r1 1:r2 2:r3 3:r4 4:avgRating 5:revealStatus 6:timestamp 7:exists
            core = contract.functions.getFeedbackCore(fid).call()
            meta = contract.functions.getFeedbackMeta(fid).call()
            if not meta[7]:  # exists
                continue

            try:
                dec_desc = decrypt_data(core[2])
            except Exception:
                dec_desc = "[DECRYPTION FAILED]"

            avg = meta[4] / 100.0 if meta[4] else 0.0
            created_at = datetime.fromtimestamp(meta[6]).isoformat() if meta[6] > 0 else "Unknown"

            feedback_list.append({
                "id": fid,
                "target_name": core[3],
                "category": core[4],
                "description": dec_desc,
                "priority": core[5],
                "created_at": created_at,
                "avg": round(avg, 2),
                "reveal_status": meta[5],   # directly from blockchain
            })

        feedback_list.sort(key=lambda x: x["created_at"], reverse=True)
    except Exception as e:
        print(f"AUTHORITY DASHBOARD BLOCKCHAIN ERROR: {e}")

    return render_template(
        "authority_dashboard.html",
        feedback_list=feedback_list,
        title="Authority Oversight",
        heading="Authority Panel"
    )


@app.route("/authority/reveal/<fb_id>", methods=["GET", "POST"])
@login_required(role="authority")
def authority_reveal(fb_id):
    is_view_only = request.method == "GET" or request.args.get("view") == "true"
    reason = request.form.get("reason") if request.method == "POST" else "Viewed session record"

    if not is_view_only and not reason:
        return "Reason is mandatory", 400

    if not contract:
        return "Blockchain not connected — cannot perform identity reveal", 503

    # ── 1. Fetch encrypted identity from Blockchain (sole source of truth) ──
    real_identity = "[NOT FOUND ON BLOCKCHAIN]"
    try:
        core = contract.functions.getFeedbackCore(str(fb_id)).call()
        meta = contract.functions.getFeedbackMeta(str(fb_id)).call()
        if not meta[7]:  # exists
            return "Feedback record not found on blockchain", 404

        # If it's a GET request but the status is NOT revealed, redirect to dashboard
        if is_view_only and meta[5] != 'revealed':
            return redirect(url_for("authority_dashboard"))

        encrypted_id = core[1]  # encryptedUser
        print(f"DEBUG: Fetched encryptedUser from Blockchain for {fb_id}")

        try:
            real_identity = decrypt_data(encrypted_id)
        except Exception as e:
            real_identity = f"Decryption Failed: {str(e)}"
    except Exception as e:
        print(f"Blockchain Fetch Error during Reveal: {e}")
        return f"Blockchain error during reveal: {str(e)}", 500

    # ── 2. Structural logic for unmasking (POST only) ──
    if request.method == "POST":
        # ── Update reveal status ON-CHAIN ──
        try:
            nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)
            txn_status = contract.functions.updateRevealStatus(str(fb_id), "revealed").build_transaction({
                "chainId": int(os.getenv("CHAIN_ID", 1337)),
                "from": ACCOUNT_ADDRESS,
                "nonce": nonce,
                "gasPrice": w3.eth.gas_price
            })
            signed_status = w3.eth.account.sign_transaction(txn_status, private_key=PRIVATE_KEY)
            w3.eth.send_raw_transaction(signed_status.raw_transaction)
            print(f"SUCCESS: updateRevealStatus('revealed') sent on-chain for {fb_id}")
        except Exception as e:
            print(f"WARNING: updateRevealStatus blockchain error for {fb_id}: {e}")

        # ── Log Identity Reveal audit ON-CHAIN ──
        try:
            nonce2 = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)
            txn_log = contract.functions.logIdentityReveal(str(fb_id), session["username"], reason).build_transaction({
                "chainId": int(os.getenv("CHAIN_ID", 1337)),
                "from": ACCOUNT_ADDRESS,
                "nonce": nonce2,
                "gasPrice": w3.eth.gas_price
            })
            signed_log = w3.eth.account.sign_transaction(txn_log, private_key=PRIVATE_KEY)
            w3.eth.send_raw_transaction(signed_log.raw_transaction)
            print(f"SUCCESS: logIdentityReveal sent on-chain for {fb_id}")
        except Exception as e:
            print(f"Blockchain Reveal Logging Error: {e}")

    return render_template(
        "reveal_result.html",
        real_identity=real_identity,
        reason=reason if request.method == "POST" else "Existing Audit Approval",
        feedback_id=fb_id,
        title="Identity Unmasked"
    )


@app.route("/authority/audit-logs")
@login_required(role="authority")
def authority_audit_logs():
    if not contract:
        return "Blockchain not connected", 503
    
    all_logs = []
    try:
        on_chain_ids = contract.functions.getAllFeedbackIds().call()
        for fid in on_chain_ids:
            # getAuditLogs(string) -> (string action, string performedBy, string reason, uint256 timestamp)[]
            logs = contract.functions.getAuditLogs(fid).call()
            for log in logs:
                all_logs.append({
                    "feedback_id": fid,
                    "action": log[0],
                    "performed_by": log[1],
                    "reason": log[2],
                    "timestamp": datetime.fromtimestamp(log[3]).isoformat() if log[3] > 0 else "Unknown"
                })
        
        # Sort logs by timestamp descending
        all_logs.sort(key=lambda x: x["timestamp"], reverse=True)
    except Exception as e:
        print(f"BLOCKCHAIN AUDIT LOG ERROR: {e}")
    
    return render_template(
        "audit_logs.html",
        logs=all_logs,
        title="Audit Logs",
        heading="Authority Audit Trail"
    )


# ---------- Main ----------
if __name__ == "__main__":
    # Note: disabled reloader to fix WinError 10038 on Windows + Python 3.13
    app.run(debug=True, use_reloader=False)
