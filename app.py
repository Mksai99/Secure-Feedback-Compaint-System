from flask import Flask, render_template, request, redirect, session, url_for
import json
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import hashlib
from cryptography.fernet import Fernet
import os

app = Flask(__name__)
app.secret_key = "any_random_long_secret_here"

# ---------- MongoDB ----------
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["feedback_platform_db"]

# Migration: Rename old collections and fields if they exist
def migrate_collections():
    # 1. Rename collections
    old_to_new = {
        "participants": "users",
        "entities": "targets",
        "moderators": "authorities"
    }
    existing_collections = db.list_collection_names()
    for old, new in old_to_new.items():
        if old in existing_collections and new not in existing_collections:
            db[old].rename(new)
    
    # 2. Rename fields in feedback collection
    db["feedback"].update_many(
        {}, 
        {"$rename": {
            "participant_hash": "user_hash", 
            "encrypted_participant_id": "encrypted_user_id"
        }}
    )

migrate_collections()

# Separate collections for each role
users_col = db["users"]             # {username, password, role="user"}
targets_col = db["targets"]         # {username, password, role="target"}
admins_col = db["admins"]           # {username, password, role="admin"}
authorities_col = db["authorities"] # {username, password, role="authority"}

feedback_col = db["feedback"]       # feedback documents
blocks_col = db["blocks"]           # blockchain
audit_col = db["audit_logs"]        # audit logs

# secret salt for user anonymity
USER_SALT = "some_fixed_random_salt"

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


def create_default_admin():
    """Create default admin user if none exists in admins collection."""
    if admins_col.count_documents({"role": "admin"}) == 0:
        admins_col.insert_one({
            "username": "admin",
            "password": "admin123",  # demo only
            "role": "admin"
        })

def create_default_authority():
    """Create default authority user if none exists."""
    if authorities_col.count_documents({"role": "authority"}) == 0:
        authorities_col.insert_one({
            "username": "authority",
            "password": "auth123",    # demo only
            "role": "authority"
        })

def get_last_block():
    last_block = blocks_col.find_one(sort=[("idx", -1)])
    if last_block:
        return {"idx": last_block["idx"], "hash": last_block["hash"]}
    return None


def create_block(feedback_id: ObjectId, feedback_data: dict):
    """
    Create a blockchain block for the given feedback
    AND update the chain_meta (head + total_blocks).
    """
    data_json = json.dumps(feedback_data, sort_keys=True)
    data_hash = sha256(data_json)

    # Get last block from blocks collection
    last_block = blocks_col.find_one(sort=[("idx", -1)])

    if last_block:
        idx = last_block["idx"] + 1
        prev_hash = last_block["hash"]
    else:
        idx = 0
        prev_hash = "0"

    timestamp = datetime.utcnow().isoformat()
    block_string = f"{idx}{timestamp}{data_hash}{prev_hash}"
    block_hash = sha256(block_string)

    # Insert new block
    blocks_col.insert_one({
        "idx": idx,
        "feedback_id": feedback_id,
        "timestamp": timestamp,
        "data_hash": data_hash,
        "prev_hash": prev_hash,
        "hash": block_hash
    })

    # ---- Update chain_meta ----
    chain_meta_col = db["chain_meta"]
    meta = chain_meta_col.find_one({"_id": "head"})

    if meta:
        total_blocks = meta.get("total_blocks", 0) + 1
    else:
        total_blocks = 1

    chain_meta_col.update_one(
        {"_id": "head"},
        {
            "$set": {
                "last_idx": idx,
                "last_hash": block_hash,
                "total_blocks": total_blocks
            }
        },
        upsert=True
    )



def verify_chain() -> bool:
    """
    Strict verification:
    - There must be at least one block
    - chain_meta must exist
    - Every block must:
        * point to an existing feedback
        * match feedback data (detect edits)
        * have correct prev_hash & hash link
    - Final block index + hash + count must match chain_meta
    """
    chain_meta_col = db["chain_meta"]
    meta = chain_meta_col.find_one({"_id": "head"})
    if not meta:
        return False

    expected_total = meta.get("total_blocks", 0)
    if expected_total <= 0:
        return False

    # Get all blocks ordered by idx
    blocks = list(blocks_col.find().sort("idx", 1))
    if not blocks:
        return False

    if len(blocks) != expected_total:
        return False

    prev_hash = "0"
    count = 0

    for b in blocks:
        count += 1

        # 1) Check link to previous block
        if b["prev_hash"] != prev_hash:
            return False

        # 2) Fetch feedback document
        fb = feedback_col.find_one({"_id": b["feedback_id"]})
        if not fb:
            return False

        # 3) Rebuild data JSON exactly as in create_block
        fb_chain = {
            "id": str(fb["_id"]),
            "target_name": fb["target_name"],
            "category": fb.get("category"),
            "description": fb["description"],
            "priority": fb.get("priority"),
            "created_at": fb["created_at"],
            "user_hash": fb["user_hash"],
            "organization_id": fb.get("organization_id"),
            "ratings": fb.get("ratings", {}),
            "average_rating": fb.get("average_rating", 0),
        }
        calc_data_hash = sha256(json.dumps(fb_chain, sort_keys=True))

        # 4) data_hash must match
        if calc_data_hash != b["data_hash"]:
            return False

        # 5) block hash must match
        calc_block_hash = sha256(
            f"{b['idx']}{b['timestamp']}{b['data_hash']}{b['prev_hash']}"
        )
        if calc_block_hash != b["hash"]:
            return False

        prev_hash = b["hash"]

    # 6) Last block must match chain_meta info
    last_block = blocks[-1]
    if last_block["idx"] != meta["last_idx"]:
        return False
    if last_block["hash"] != meta["last_hash"]:
        return False
    if count != expected_total:
        return False

    return True



def current_user():
    if "username" in session:
        return {
            "username": session["username"],
            "role": session["role"]
        }
    return None


def login_required(role=None):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return redirect(url_for("login"))
            if role and user["role"] != role:
                return "Unauthorized", 403
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
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        # choose collection based on role
        if role == "user":
            col = users_col
        elif role == "target":
            col = targets_col
        elif role == "admin":
            col = admins_col
        elif role == "authority":
            col = authorities_col
        else:
            col = None

        user = None
        if col is not None:
            user = col.find_one({"username": username, "password": password, "role": role})

        if user:
            session["username"] = username
            session["role"] = role
            if role == "user":
                return redirect(url_for("user_submit_feedback"))
            elif role == "target":
                return redirect(url_for("target_view_feedback"))
            elif role == "authority":
                return redirect(url_for("authority_dashboard"))
            else:
                return redirect(url_for("admin_dashboard"))
        else:
            return render_template(
                "login.html",
                error="Invalid credentials",
                title="Login",
                heading="Login",
            )

    return render_template("login.html", error=None, title="Login", heading="Login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ----- User -----
@app.route("/user/provide-feedback", methods=["GET", "POST"])
@login_required(role="user")
def user_submit_feedback():
    if request.method == "POST":
        target_name = request.form.get("target_username")
        category = request.form.get("category")
        description = request.form.get("description")
        priority = request.form.get("priority", "Medium")
        created_at = datetime.utcnow().isoformat()

        # optional indicator ratings
        rating_1 = int(request.form.get("rating_1", 0))
        rating_2 = int(request.form.get("rating_2", 0))
        rating_3 = int(request.form.get("rating_3", 0))
        rating_4 = int(request.form.get("rating_4", 0))

        avg_rating = round((rating_1 + rating_2 + rating_3 + rating_4) / 4.0, 2)

        user_username = session["username"]
        # anonymized user id
        user_hash = sha256(user_username + USER_SALT)

        feedback_doc = {
            "target_name": target_name,
            "category": category,
            "description": description,
            "priority": priority,
            "created_at": created_at,
            "user_hash": user_hash,
            "organization_id": "ORG-001", # static demo ID
            "ratings": {
                "indicator_1": rating_1,
                "indicator_2": rating_2,
                "indicator_3": rating_3,
                "indicator_4": rating_4,
            },
            "average_rating": avg_rating,
            "deleted": False,
            "encrypted_user_id": encrypt_data(user_username),
            "reveal_status": "sealed",
        }

        result = feedback_col.insert_one(feedback_doc)
        feedback_id = result.inserted_id

        # blockchain data
        fb_for_chain = {
            "id": str(feedback_id),
            "target_name": target_name,
            "category": category,
            "description": description,
            "priority": priority,
            "created_at": created_at,
            "user_hash": user_hash,
            "organization_id": feedback_doc["organization_id"],
            "ratings": feedback_doc["ratings"],
            "average_rating": avg_rating,
        }
        create_block(feedback_id, fb_for_chain)

        return redirect(url_for("user_submit_feedback"))

    # GET – show form with targets list
    target_list = list(
        targets_col.find({"role": "target"}, {"username": 1, "_id": 0})
    )
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
    fbs = list(
        feedback_col.find({
            "target_name": target_username,
            "deleted": {"$ne": True}
        }).sort("created_at", -1)
    )

    feedback_list = []
    for f in fbs:
        ratings = f.get("ratings", {})
        feedback_list.append(
            {
                "category": f.get("category"),
                "description": f.get("description"),
                "priority": f.get("priority"),
                "created_at": f.get("created_at"),
                "avg": f.get("average_rating", 0),
                "ind1": ratings.get("indicator_1", "-"),
                "ind2": ratings.get("indicator_2", "-"),
                "ind3": ratings.get("indicator_3", "-"),
                "ind4": ratings.get("indicator_4", "-"),
            }
        )

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
    target_list = list(targets_col.find({"role": "target"}, {"username": 1, "_id": 0}))
    fbs = list(
        feedback_col.find({
            "deleted": {"$ne": True}
        }).sort("created_at", -1)
    )

    feedback_list = []
    for f in fbs:
        feedback_list.append(
            {
                "id": str(f["_id"]),
                "target_name": f.get("target_name"),
                "category": f.get("category"),
                "description": f.get("description"),
                "priority": f.get("priority"),
                "created_at": f.get("created_at"),
                "avg": f.get("average_rating", 0),
            }
        )

    chain_valid = verify_chain()
    return render_template(
        "admin_dashboard.html",
        target_list=target_list,
        feedback_list=feedback_list,
        chain_valid=chain_valid,
        title="Administrator Control Center",
        heading="Platform Administration",
    )


@app.route("/admin/add-target", methods=["POST"])
@login_required(role="admin")
def admin_add_target():
    username = request.form.get("username")
    password = request.form.get("password")
    if username and password:
        targets_col.insert_one({"username": username, "password": password, "role": "target"})
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/add-user", methods=["POST"])
@login_required(role="admin")
def admin_add_user():
    username = request.form.get("username")
    password = request.form.get("password")
    if username and password:
        users_col.insert_one({"username": username, "password": password, "role": "user"})
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete-target/<username>", methods=["POST"])
@login_required(role="admin")
def admin_delete_target(username):
    targets_col.delete_one({"username": username, "role": "target"})
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete-feedback/<fb_id>", methods=["POST"])
@login_required(role="admin")
def admin_delete_feedback(fb_id):
    try:
        rid = ObjectId(fb_id)
    except Exception:
        return redirect(url_for("admin_dashboard"))

    feedback_col.update_one(
        {"_id": rid},
        {"$set": {"deleted": True, "deleted_at": datetime.utcnow().isoformat()}}
    )
    return redirect(url_for("admin_dashboard"))


# ----- Authority -----
@app.route("/authority")
@login_required(role="authority")
def authority_dashboard():
    fbs = list(
        feedback_col.find({
            "deleted": {"$ne": True}
        }).sort("created_at", -1)
    )

    feedback_list = []
    for f in fbs:
        feedback_list.append({
            "id": str(f["_id"]),
            "target_name": f.get("target_name"),
            "category": f.get("category"),
            "description": f.get("description"),
            "priority": f.get("priority"),
            "created_at": f.get("created_at"),
            "avg": f.get("average_rating", 0),
            "reveal_status": f.get("reveal_status", "sealed"),
        })

    return render_template(
        "authority_dashboard.html",
        feedback_list=feedback_list,
        title="Authority Oversight",
        heading="Authority Panel"
    )


@app.route("/authority/reveal/<fb_id>", methods=["POST"])
@login_required(role="authority")
def authority_reveal(fb_id):
    reason = request.form.get("reason")
    if not reason:
        return "Reason is mandatory", 400

    try:
        rid = ObjectId(fb_id)
    except:
        return "Invalid ID", 400

    fb = feedback_col.find_one({"_id": rid})
    if not fb:
        return "Feedback record not found", 404

    # Decrypt
    encrypted_id = fb.get("encrypted_user_id")
    real_identity = "Unknown (Manual Entry)"
    if encrypted_id:
        try:
            real_identity = decrypt_data(encrypted_id)
        except Exception as e:
            real_identity = f"Decryption Failed: {str(e)}"

    # Update status
    feedback_col.update_one(
        {"_id": rid},
        {"$set": {"reveal_status": "revealed"}}
    )

    # Log to Audit
    audit_col.insert_one({
        "feedback_id": str(rid),
        "action": "IDENTITY_REVEAL",
        "performed_by": session["username"],
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    })

    return render_template(
        "reveal_result.html",
        real_identity=real_identity,
        reason=reason,
        feedback_id=fb_id,
        title="Identity Unmasked"
    )


@app.route("/authority/audit-logs")
@login_required(role="authority")
def authority_audit_logs():
    logs = list(audit_col.find().sort("timestamp", -1))
    return render_template(
        "audit_logs.html",
        logs=logs,
        title="Audit Logs",
        heading="Authority Audit Trail"
    )


# ---------- Main ----------
if __name__ == "__main__":
    create_default_admin()
    create_default_authority()
    # Disabling the reloader for maximum stability on Windows with Python 3.13.
    # Note: You must manually restart the server after code changes.
    app.run(debug=True, use_reloader=False)
