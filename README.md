# 🛡️ Secure Feedback & Complaint System (SFCS)
### "Where Transparency Meets Absolute Privacy"

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Web3.py](https://img.shields.io/badge/Web3.py-6.11.1-F16822?style=for-the-badge&logo=ethereum&logoColor=white)](https://web3py.readthedocs.io/)
[![Supabase](https://img.shields.io/badge/Supabase-Auth-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)

---

## 📖 Project Description

### 🚩 The Problem
In many organizations, the fear of retaliation often prevents honest feedback and reporting of complaints. Traditional databases are centralized and can be manipulated by administrators, leading to a lack of trust in "anonymous" systems.

### 💡 The Solution
The **Secure Feedback System (SFCS)** is an institutional-grade, privacy-preserving platform that leverages **Blockchain Technology** to ensure absolute data integrity. By using a decentralized ledger as the **Single Source of Truth (SSOT)**, it renders unauthorized data manipulation or deletion technically impossible. Identities are cryptographically shielded, and "unmasking" is only possible through strict moderator oversight with an immutable audit trail.

---

## ✨ Features

- **🔗 Pure Blockchain Storage**: Every feedback entry is stored directly on an Ethereum-compatible decentralized ledger (Ganache). No centralized database stores the core feedback content.
- **🔐 Cryptographic Anonymity**: Participant identities are encrypted using **AES-256 (Fernet)**. Even system administrators cannot see who provided specific feedback.
- **🕵️ Controlled De-anonymization**: The `Authority/Moderator` role can initiate a reveal only under verified policy necessity. Every reveal requires a mandatory justification and is logged permanently on the blockchain.
- **👥 Advanced RBAC (Role-Based Access Control)**:
  - **Participant**: Provides anonymous feedback and complaints.
  - **Entity/Target**: Receives and views feedback targeted at them.
  - **Admin**: Manages organizational directory and system health via Supabase.
  - **Authority**: High-level oversight and identity auditing.
- **📧 Secure Account Lifecycle**: Fully integrated **Supabase Auth** with email verification, password recovery, and secure invite systems.
- **📊 Real-time Analytics**: Dashboard provides live platform stats directly from the blockchain state.

---

## 🛠️ Tech Stack

### Frontend
- **Structure**: HTML5 Semantic Markup
- **Styling**: CSS3 (Modern "Institutional" Theme), Bootstrap 5
- **Icons**: FontAwesome / Lucide

### Backend
- **Framework**: Python (Flask)
- **Security**: Cryptography (AES-256 Fernet), Hashlib (SHA-256)
- **Email**: Flask-Mail (SMTP Integration)

### Blockchain & Database
- **Core Storage**: Ethereum Smart Contract (Solidity)
- **Local Provider**: Ganache (RPC Node)
- **Auth & User Management**: Supabase (Cloud Authentication)
- **Communication**: Web3.py

---

## 📂 Project Structure

```text
Secure-Feedback-System/
├── .agent/              # AI Agent configuration
├── .env                 # Environment variables (Secrets)
├── .env.example         # Template for environment variables
├── app.py               # Main Flask Application (Routes & Logic)
├── check_blockchain.py  # Utility to verify blockchain state
├── contract_artifacts.json # Compiled Smart Contract details
├── contracts/           # Solidity Smart Contracts
│   └── FeedbackPortal.sol
├── deploy.py            # Blockchain deployment script
├── how_to_run.md        # Detailed setup guide
├── requirements.txt     # Python Dependencies
├── run_project.bat      # Quick-start script for Windows
├── secret.key           # Fernet encryption key (Auto-generated)
├── static/              # CSS, JS, and Images
└── templates/           # HTML Templates (Jinja2)
```

---

## ⚙️ Installation & Setup

### 1️⃣ Prerequisites
- **Python 3.8+**
- **Node.js** (for Ganache)
- **Supabase Account** (Free tier works)
- **Ganache** (CLI or GUI)

### 2️⃣ Clone the Repository
```bash
git clone https://github.com/Mksai99/Secure-Feedback-System.git
cd Secure-Feedback-System
```

### 3️⃣ Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables
Create a `.env` file from the example:
```bash
cp .env.example .env
```
Fill in your **Supabase URL**, **Anon Key**, and **Ganache RPC Details**.

### 5️⃣ Deploy Smart Contract
Start Ganache, then run:
```bash
python deploy.py
```

### 6️⃣ Run the App
```bash
python app.py
```
Access the application at `http://127.0.0.1:5000`.

---

## 🖼️ Screenshots

### 🏠 Home Screen
The public-facing landing page communicates the platform's core value proposition — anonymity, immutability, and ethical moderation — before a user logs in.

![Home Screen](screenshots/Home_Screen.png)

---

### 🔐 Login
Role-aware login portal. All sessions are JWT-secured via Supabase Auth. Supports password visibility toggle and "Forgot Password" recovery flow.

![Login](screenshots/Login.png)

---

### 🔑 Password Recovery
Users can request a secure reset link sent to their registered organizational email address.

![Password Recovery](screenshots/Password_recovery.png)

---

### 📝 Give Feedback (Participant View)
Participants submit feedback or formal complaints anonymously. They can choose the submission type (General Feedback or Formal Complaint), select a target entity, rate across multiple indicators (Quality, Communication, Timeliness, Reliability), and add a description. All data is encrypted and written to the blockchain.

![Give Feedback](screenshots/Give_Feedback.png)

---

### 📥 Target Feedback View
Targets (entities receiving feedback) see their inbox of all submissions. Identities of submitters are fully hidden — protected by cryptographic encryption. Only the Authority can unmask them under verified circumstances.

![Target Feedback View](screenshots/Target_Feedback_View.png)

---

### 🖥️ Admin Dashboard
Administrators manage the full user directory and can view the blockchain feedback ledger. Key functions include adding new Targets and Users (via email invite), and monitoring all submissions marked **IMMUTABLE** on the chain. The dashboard header shows real-time **Blockchain: VERIFIED** and **Session: JWT SECURED** status.

![Admin Dashboard](screenshots/Admin_Dashboard.png)

---

### 🛡️ Authority Dashboard (Oversight Authority Control)
The Authority role has a specialized control panel for auditing all feedback submissions. Each record displays recipient, type, classification, priority, satisfaction score, a content snippet, and an **ENCRYPTED** access control badge. The **Unmask** button initiates the de-anonymization flow.

![Authority Dashboard](screenshots/Authority_Dashboard.png)

---

### 🔓 Identity Reveal Request
Before unmasking, the Authority must provide a mandatory **Case Reference / Justification**. A critical warning makes clear that this action is permanently recorded on the blockchain ledger, and unauthorized use may lead to disciplinary action.

![Identity Reveal Request](screenshots/Identity_reveal_request.png)

---

### 🪪 Identity Reveal Result
Upon successful de-anonymization, the system displays the **Verified User Identity**, confirms **Integrity Verified** status, and shows the recorded justification. The entire transaction is framed with a red "RESTRICTED ACCESS • IDENTITY UNMASKED" banner to underscore the gravity of the action.

![Identity Reveal](screenshots/Identity_reveal.png)

---

### 📋 Ledger Audit (System Audit Trail)
A transparent, tamper-proof log of all authority actions on the platform. Each entry records the UTC timestamp, auditor name, action type (e.g., `IDENTITY_REVEAL`), the feedback reference ID, and the mandatory justification provided. The chain integrity is confirmed with a **CHAIN VERIFIED** badge.

![Ledger Audit](screenshots/Ledger_Audit.png)

---

## 🚀 Usage

1. **Admin Login**: Log in using the admin credentials to create Users and Targets.
2. **Invite Users**: The system sends email invites via Supabase to allow users to set their own passwords.
3. **Submit Feedback**: Log in as a 'User' to submit a complaint or feedback. The data is hashed and pushed to the blockchain immediately.
4. **View Feedback**: Log in as a 'Target' to see what people think of your performance (anonymously).
5. **Audit**: Log in as 'Authority' to verify the integrity of the chain or unmask an identity if a serious violation is reported.

---

## 📡 API Endpoints

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Platform statistics dashboard | Public |
| `POST` | `/login` | User authentication | Public |
| `POST` | `/user/provide-feedback` | Submit data to blockchain | Participant |
| `GET` | `/target/view-feedback` | View entries for self | Target |
| `GET` | `/authority/reveal/<id>` | Unmask user identity | Authority |
| `GET` | `/admin` | User management center | Admin |

---

## 🏗️ Architecture Overview

The SFCS follows a **Hybrid Blockchain Architecture**:
1. **Frontend (Flask templates)** sends data to the **Flask Server**.
2. **Supabase** validates the JWT session and confirms the user's role.
3. The **Flask Server** encrypts the identity and hashes the feedback content.
4. The **Web3 Layer** interacts with the **Smart Contract** to store the hash and encrypted data permanently.
5. **Blockchain** returns a transaction confirmation, which is then shown to the user.

---

## 🎓 Learning Outcomes
- **Distributed Ledgers**: Deep understanding of how to use blockchain as a tamper-proof storage layer.
- **Cloud Identity**: Integrating enterprise-grade Auth (Supabase) with local backend logic.
- **Cryptography**: Implementing AES-256 for data-at-rest and SHA-256 for integrity verification.
- **Professional UX**: Building complex multi-role dashboards with a consistent design language.

---

## 🚧 Challenges & Solutions
- **Challenge**: Network latency during blockchain writes on slow RPCs.
  - **Solution**: Implemented a **Transaction Retry Mechanism** with exponential backoff in `app.py`.
- **Challenge**: Maintaining anonymity while allowing for accountability.
  - **Solution**: Developed a **Two-Tier Identity Layer** where the real identity is encrypted and stored, but the "key" to unmask it is protected by role-based smart contract logic.

---

## 🔮 Future Improvements
- [ ] **Multi-Org Support**: Allow multiple organizations to host their own feedback nodes.
- [ ] **IPFS Integration**: Move larger attachments/evidence to IPFS while keeping the CID on the blockchain.
- [ ] **Mobile App**: Develop a Flutter/React Native app for on-the-go reporting.

---

## 🤝 Contributing
Contributions are welcome! Please follow these steps:
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

---

## 👤 Author
**Krishna Sai**
- GitHub: [@Mksai99](https://github.com/Mksai99)
- Portfolio: [Check out my work!](https://github.com/Mksai99)

---
*Made with ❤️ for a more transparent future.*
