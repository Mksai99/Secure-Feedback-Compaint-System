# Secure Anonymous Feedback and Complaint System

The **Secure Anonymous Feedback and Complaint System** is a next-generation, institutional-grade solution engineered to facilitate honest communication within organizations while ensuring absolute data integrity and identity protection. By implementing a **Pure Blockchain Storage** model, the platform establishes the decentralized ledger as the **Single Source of Truth (SSOT)** for all feedback and complaint records, rendering unauthorized data manipulation or deletion technically impossible.

Built on a modern stack comprising **Flask**, **Supabase (Auth)**, and a **custom Ethereum-based smart contract**, the system addresses the critical challenge of maintaining institutional trust. Every submission is cryptographically secured using **SHA-256 hash-linking** and stored directly on-chain. Participant identities and sensitive descriptions are further protected using **AES-256 (Fernet) encryption**, ensuring that even system administrators cannot unmask contributors.

To balance transparency with accountability, the system features a granular **Role-Based Access Control (RBAC)** framework with four distinct roles: **Participant, Entity, Admin, and Moderator**. Professional oversight is maintained by Moderators, who possess strictly audited authority to initiate identity unmasking only under verified policy necessity, with every action recorded in an immutable audit trail. This comprehensive, blockchain-first approach converts feedback from a potential liability into a verified strategic asset, empowering communities to foster a culture of transparency without compromising individual security.

## 🚀 Key Features

### 🔐 Security & Integrity
- **Pure Blockchain Storage**: Every feedback entry is stored directly on a decentralized ledger. Unauthorized modification or deletion is technically impossible, with full verification handled by on-chain smart contracts.
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
- **Authentication**: Supabase (Auth/REST)
- **Core Storage**: Immutable Blockchain Ledger (Single Source of Truth)
- **Frontend**: HTML5, CSS3, Bootstrap 5 (Custom "Institutional" Theme)
- **Cryptography**: `hashlib` (SHA-256), `cryptography` (AES-256 Fernet)
- **Integrity Layer**: Ethereum Smart Contract (Web3)

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- Supabase Project (configured in .env)
- Local or Remote Ethereum RPC Node (e.g. Ganache or Alchemy)

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
