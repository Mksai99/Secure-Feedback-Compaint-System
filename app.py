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
db = client["feedback_blockchain_db"]

# Separate collections for each role
students_col = db["students"]     # {username, password, role="student"}
faculty_col = db["faculty"]       # {username, password, role="faculty"}
admins_col = db["admins"]         # {username, password, role="admin"}
authority_col = db["authority"]   # {username, password, role="authority"} -- NEW

feedback_col = db["feedback"]     # feedback documents
blocks_col = db["blocks"]         # blockchain
audit_col = db["audit_logs"]      # audit logs -- NEW

feedback_col = db["feedback"]     # feedback documents
blocks_col = db["blocks"]         # blockchain

# secret salt for student anonymity
ANON_SALT = "some_fixed_random_salt"


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
    if authority_col.count_documents({"role": "authority"}) == 0:
        authority_col.insert_one({
            "username": "authority",
            "password": "auth123",  # demo only
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

    # ---- NEW: update chain_meta ----
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
        # No head info -> can't trust chain
        return False

    expected_total = meta.get("total_blocks", 0)
    if expected_total <= 0:
        return False

    # Get all blocks ordered by idx
    blocks = list(blocks_col.find().sort("idx", 1))
    if not blocks:
        # No blocks but meta says there should be
        return False

    if len(blocks) != expected_total:
        # Someone deleted or added blocks
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
            # Block points to feedback that no longer exists
            return False

        # 3) Rebuild data JSON exactly as in create_block
        fb_chain = {
            "id": str(fb["_id"]),
            "faculty_username": fb["faculty_username"],
            "course": fb.get("course"),
            "comments": fb["comments"],
            "created_at": fb["created_at"],
            "student_hash": fb["student_hash"],
            "ratings": fb["ratings"],
            "average_rating": fb["average_rating"],
        }
        calc_data_hash = sha256(json.dumps(fb_chain, sort_keys=True))

        # 4) data_hash must match
        if calc_data_hash != b["data_hash"]:
            # Feedback was edited
            return False

        # 5) block hash must match
        calc_block_hash = sha256(
            f"{b['idx']}{b['timestamp']}{b['data_hash']}{b['prev_hash']}"
        )
        if calc_block_hash != b["hash"]:
            # Block content was edited
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
        title="Secure Feedback System",
        heading="Secure Feedback System",
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        # choose collection based on role
        if role == "student":
            col = students_col
        elif role == "faculty":
            col = faculty_col
        elif role == "admin":
            col = admins_col
        elif role == "authority":
            col = authority_col
        else:
            col = None

        user = None
        if col is not None:
            user = col.find_one({"username": username, "password": password, "role": role})

        if user:
            session["username"] = username
            session["role"] = role
            if role == "student":
                return redirect(url_for("student_feedback"))
            elif role == "faculty":
                return redirect(url_for("faculty_feedbacks"))
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


# ----- Student -----
@app.route("/student/feedback", methods=["GET", "POST"])
@login_required(role="student")
def student_feedback():
    if request.method == "POST":
        faculty_username = request.form.get("faculty_username")
        course = request.form.get("course")
        comments = request.form.get("comments")
        created_at = datetime.utcnow().isoformat()

        # 4 criteria ratings (1–5)
        rating_knowledge = int(request.form.get("rating_knowledge"))
        rating_communication = int(request.form.get("rating_communication"))
        rating_punctuality = int(request.form.get("rating_punctuality"))
        rating_support = int(request.form.get("rating_support"))

        avg_rating = round(
            (rating_knowledge
             + rating_communication
             + rating_punctuality
             + rating_support) / 4.0,
            2,
        )

        student_username = session["username"]
        # anonymized student id (not shown anywhere)
        student_hash = sha256(student_username + ANON_SALT)

        fb_doc = {
            "faculty_username": faculty_username,
            "course": course,
            "comments": comments,
            "created_at": created_at,
            "student_hash": student_hash,
            "ratings": {
                "knowledge": rating_knowledge,
                "communication": rating_communication,
                "punctuality": rating_punctuality,
                "support": rating_support,
            },
            "average_rating": avg_rating,
            "deleted": False,   # for soft delete
            # --- NEW: Controlled Anonymity Fields ---
            "encrypted_student_id": encrypt_data(student_username),
            "reveal_status": "sealed",  # sealed | revealed
        }

        result = feedback_col.insert_one(fb_doc)
        fb_id = result.inserted_id

        # data used on blockchain (still anonymous)
        fb_for_chain = {
            "id": str(fb_id),
            "faculty_username": faculty_username,
            "course": course,
            "comments": comments,
            "created_at": created_at,
            "student_hash": student_hash,
            "ratings": fb_doc["ratings"],
            "average_rating": avg_rating,
        }
        create_block(fb_id, fb_for_chain)

        return redirect(url_for("student_feedback"))

    # GET – show form with faculty list
    faculty_list = list(
        faculty_col.find({"role": "faculty"}, {"username": 1, "_id": 0})
    )
    return render_template(
        "student_feedback.html",
        faculty_list=faculty_list,
        title="Student Feedback",
        heading="Student Panel",
    )


# ----- Faculty -----
@app.route("/faculty/feedbacks")
@login_required(role="faculty")
def faculty_feedbacks():
    faculty_username = session["username"]
    fbs = list(
        feedback_col.find({
            "faculty_username": faculty_username,
            "deleted": {"$ne": True}
        }).sort("created_at", -1)
    )

    feedbacks = []
    for fb in fbs:
        ratings = fb.get("ratings", {})
        feedbacks.append(
            {
                "course": fb.get("course"),
                "comments": fb.get("comments"),
                "created_at": fb.get("created_at"),
                "avg": fb.get("average_rating", 0),
                "knowledge": ratings.get("knowledge", "-"),
                "communication": ratings.get("communication", "-"),
                "punctuality": ratings.get("punctuality", "-"),
                "support": ratings.get("support", "-"),
            }
        )

    return render_template(
        "faculty_feedbacks.html",
        feedbacks=feedbacks,
        title="Faculty Feedbacks",
        heading="Faculty Panel",
    )


# ----- Admin -----
@app.route("/admin")
@login_required(role="admin")
def admin_dashboard():
    faculty_list = list(faculty_col.find({"role": "faculty"}, {"username": 1, "_id": 0}))
    fbs = list(
        feedback_col.find({
            "deleted": {"$ne": True}
        }).sort("created_at", -1)
    )

    feedbacks = []
    for fb in fbs:
        ratings = fb.get("ratings", {})
        feedbacks.append(
            {
                "id": str(fb["_id"]),
                "faculty_username": fb.get("faculty_username"),
                "course": fb.get("course"),
                "comments": fb.get("comments"),
                "created_at": fb.get("created_at"),
                "avg": fb.get("average_rating", 0),
                "knowledge": ratings.get("knowledge", "-"),
                "communication": ratings.get("communication", "-"),
                "punctuality": ratings.get("punctuality", "-"),
                "support": ratings.get("support", "-"),
            }
        )

    chain_valid = verify_chain()
    return render_template(
        "admin_dashboard.html",
        faculty_list=faculty_list,
        feedbacks=feedbacks,
        chain_valid=chain_valid,
        title="Admin Dashboard",
        heading="Admin Panel",
    )


@app.route("/admin/add-faculty", methods=["POST"])
@login_required(role="admin")
def admin_add_faculty():
    username = request.form.get("username")
    password = request.form.get("password")
    if username and password:
        faculty_col.insert_one({"username": username, "password": password, "role": "faculty"})
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/add-student", methods=["POST"])
@login_required(role="admin")
def admin_add_student():
    username = request.form.get("username")
    password = request.form.get("password")
    if username and password:
        students_col.insert_one({"username": username, "password": password, "role": "student"})
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete-faculty/<username>", methods=["POST"])
@login_required(role="admin")
def admin_delete_faculty(username):
    # Only delete users who are actually faculty
    faculty_col.delete_one({"username": username, "role": "faculty"})
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete-feedback/<feedback_id>", methods=["POST"])
@login_required(role="admin")
def admin_delete_feedback(feedback_id):
    """
    Soft delete feedback: mark as deleted = True, keep it in DB + blockchain.
    This keeps blockchain history intact but hides it from UI.
    """
    try:
        fid = ObjectId(feedback_id)
    except Exception:
        return redirect(url_for("admin_dashboard"))

    feedback_col.update_one(
        {"_id": fid},
        {"$set": {"deleted": True, "deleted_at": datetime.utcnow().isoformat()}}
    )
    return redirect(url_for("admin_dashboard"))


# ----- Authority -----
@app.route("/authority")
@login_required(role="authority")
def authority_dashboard():
    # Only show non-deleted feedback (or show all? admin shows non-deleted).
    # Authority needs to be able to audit feedback.
    # We will show same list as admin.
    fbs = list(
        feedback_col.find({
            "deleted": {"$ne": True}
        }).sort("created_at", -1)
    )

    feedbacks = []
    for fb in fbs:
        ratings = fb.get("ratings", {})
        feedbacks.append({
            "id": str(fb["_id"]),
            "faculty_username": fb.get("faculty_username"),
            "course": fb.get("course"),
            "comments": fb.get("comments"),
            "created_at": fb.get("created_at"),
            "avg": fb.get("average_rating", 0),
            "reveal_status": fb.get("reveal_status", "sealed"),  # Show status
            # Do NOT show encrypted_student_id or real identity here by default
        })

    return render_template(
        "authority_dashboard.html",
        feedbacks=feedbacks,
        title="Authority Dashboard",
        heading="Authority Panel"
    )


@app.route("/authority/reveal/<feedback_id>", methods=["POST"])
@login_required(role="authority")
def authority_reveal(feedback_id):
    reason = request.form.get("reason")
    if not reason:
        # Reason is mandatory
        return "Reason is mandatory", 400

    try:
        fid = ObjectId(feedback_id)
    except:
        return "Invalid ID", 400

    fb = feedback_col.find_one({"_id": fid})
    if not fb:
        return "Feedback not found", 404

    # Check if already revealed? Even if yes, we can reveal again or just show it.
    # But we update status.

    # Decrypt
    encrypted_id = fb.get("encrypted_student_id")
    real_identity = "Unknown (Legacy)"
    if encrypted_id:
        try:
            real_identity = decrypt_data(encrypted_id)
        except Exception as e:
            real_identity = f"Decryption Failed: {str(e)}"

    # Update status
    feedback_col.update_one(
        {"_id": fid},
        {"$set": {"reveal_status": "revealed"}}
    )

    # Log to Audit
    audit_col.insert_one({
        "feedback_id": str(fid),
        "action": "IDENTITY_REVEAL",
        "performed_by": session["username"],
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Show the identity to the Authority
    # We can render a simple result page or flash it.
    # For a specialized flow, let's render a "reveal_result.html" or just reuse a template.
    # I'll create a simple string return or a small template for "Identity Revealed".
    return render_template(
        "authority_reveal_result.html",
        real_identity=real_identity,
        reason=reason,
        feedback_id=feedback_id,
        title="Identity Revealed"
    )


@app.route("/authority/audit-logs")
@login_required(role="authority")
def authority_audit_logs():
    logs = list(audit_col.find().sort("timestamp", -1))
    return render_template(
        "audit_logs.html",
        logs=logs,
        title="Audit Logs",
        heading="Audit Logs"
    )


# ---------- Main ----------
if __name__ == "__main__":
    create_default_admin()
    create_default_authority()
    app.run(debug=True)
