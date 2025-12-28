# Secure Feedback System (Blockchain-backed)

## Project Name

Secure Feedback System (Blockchain-backed)

## Idea

Build a simple web app to collect student feedback while preserving anonymity and ensuring tamper-evidence by recording each feedback as a block in a lightweight blockchain stored in MongoDB.

## Problem Statement

Traditional feedback systems are vulnerable to tampering and may expose student identities. Institutions need a simple way to collect honest feedback while maintaining student anonymity and a verifiable audit trail that detects edits or deletions.

## Solution

This project implements a role-based Flask web application where:
- Students submit anonymous feedback (anonymized via a salted hash).
- Each feedback entry is stored in MongoDB and a corresponding block is appended to a local blockchain collection, linking blocks by hashes to make tampering detectable.
- Faculty can view feedback about themselves without seeing student identities.
- Admins can manage users and verify the integrity of the stored chain.

## Technologies Used

- **Python 3.x**
- **Flask** — web framework
- **pymongo / MongoDB** — data storage for users, feedback, and blockchain
- **Bootstrap 5** — UI styling (via CDN)

Refer to dependencies in [requirements.txt](requirements.txt).

## Methodology

1. Role-based authentication (student, faculty, admin).
2. Students submit feedback with ratings + comments. The app computes an anonymized `student_hash` by hashing the username with a fixed salt.
3. Feedback is inserted into the `feedback` collection in MongoDB.
4. A block is created using a deterministic JSON of the feedback, hashed (SHA-256) and linked to the previous block hash. Blocks are stored in the `blocks` collection and a `chain_meta` collection keeps head/total information.
5. Admins can run a verification routine that recalculates data hashes and block hashes and validates the chain meta to detect tampering or edits.

Files of interest:
- [app.py](app.py)
- Templates: [templates/base.html](templates/base.html), [templates/login.html](templates/login.html), [templates/student_feedback.html](templates/student_feedback.html), [templates/faculty_feedbacks.html](templates/faculty_feedbacks.html), [templates/admin_dashboard.html](templates/admin_dashboard.html)

## Advantages

- Student anonymity: identities replaced by a salted hash so feedback stays private.
- Tamper-evidence: blockchain-style linking of feedback detects edits or deletions.
- Lightweight and self-contained: uses MongoDB collections (no external blockchain network required).
- Role-based UX: separate views & permissions for students, faculty, and admins.

## Upgradations (Future Improvements)

- Replace fixed salt with per-instance configuration or use HSM for secure salts.
- Use proper password hashing (bcrypt/argon2) and registration flow instead of storing plaintext demo passwords.
- Add email verification and password reset flows.
- Add pagination, search and export (CSV/PDF) for admin reports.
- Integrate digital signatures for stronger non-repudiation guarantees.
- Add automated tests and a CI pipeline, containerization (`Dockerfile`) and deployment docs.
- Support remote hosted MongoDB (Atlas) with secure credentials from environment variables.

## How to Run (local development)

1. Ensure MongoDB is running locally (default on `mongodb://localhost:27017/`).
2. Create and activate a Python virtual environment.

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

3. Start the Flask app:

```powershell
python app.py
```

4. Open `http://localhost:5000` in your browser.

Notes:
- The app creates a default admin (`admin` / `admin123`) if no admin exists. Change credentials before production use.
- For production, set `app.secret_key` securely and configure MongoDB credentials via environment variables.

## Project Structure

- [app.py](app.py) — main Flask application and blockchain logic
- [requirements.txt](requirements.txt) — Python dependencies
- templates/ — Jinja2 HTML templates

## Next Steps / For Your GitHub Profile

- Add a short project description and screenshots to this `README.md`.
- Add a `LICENSE` and `CONTRIBUTING.md` if you intend to make the repo public.
- Add a small `Demo.md` or GIF showing the workflow (login → submit feedback → verify chain).

---

If you want, I can also:
- add screenshots or a demo GIF,
- add a `Dockerfile` and `docker-compose.yml` for easy deployment, or
- create a short `CONTRIBUTING.md` and `LICENSE`.
