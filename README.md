# Secure Anonymous Feedback Platform (Blockchain-Backed)

A privacy-first, enterprise-grade anonymous feedback platform built with **Flask**, **MongoDB**, and **Immutable Hash-Based Blockchain** Technology. This system allows organizations, communities, and services to collect honest, anonymous feedback while ensuring data integrity and strictly controlled identity protection.

## 🚀 Key Features

### 🔐 Security & Integrity
- **Blockchain Verification**: Every feedback entry is cryptographically linked to the previous one via SHA-256 hashing. Any unauthorized modification or deletion invalidates the chain, detectable via the Admin Control Center.
- **Identity Protection**: Participant identities are encrypted using AES-256 (Fernet). Entities and Admins cannot see who provided the feedback.
- **Controlled De-anonymization**: Only the `Moderator` role can unmask a participant's identity, and **every action is logged** in an immutable audit ledger with a mandatory justification.

### 👥 Role-Based Access Control
The system features four distinct roles:
1. **Participant**: Can provide anonymous feedback with various indicators (Quality, Communication, etc.) and priority levels.
2. **Entity**: Recipients of feedback who can view entries targetted at them (anonymously).
3. **Admin**: Manages the user directory (Entities/Participants), performs maintenance, and monitors system health.
4. **Moderator**: Professional oversight role authorized to audit feedback and initiate identity unmasking for verified policy necessity.

### 🎨 Modern UI/UX
- **Institutional Design**: A clean, light-first professional interface using a professional blue and trustworthy teal palette.
- **Dashboard-Centric**: Intuitive navigation with a modern sidebar and role-specific views.
- **Real-time Integrity**: Visual indicators for blockchain validity and a transparent audit trail for system accountability.

---

## 🛠️ Technology Stack
- **Backend**: Python (Flask)
- **Database**: MongoDB (NoSQL)
- **Frontend**: HTML5, CSS3, Bootstrap 5 (Custom "Institutional" Theme)
- **Cryptography**: `hashlib` (SHA-256), `cryptography` (AES-256 Fernet)
- **Data Integrity**: Custom Hash-Chain Implementation

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB (Running locally on default port `27017`)

### 1. Clone the Repository
```bash
git clone https://github.com/Mksai99/Secure-Feedback-System.git
cd Secure-Feedback-System
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```
*Note: On the first run, a `secret.key` file will be generated. This key is used to decrypt participant identities and must be guarded as a high-security asset.*

---

## 👤 Default Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| **Administrator** | `admin` | `admin123` |
| **Moderator** | `moderator` | `mod123` |

*Participant and Entity accounts can be provisioned via the Admin Control Center.*

---

## 🛡️ License
This project is for educational and professional portfolio purposes.
