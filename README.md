# Secure Feedback System (Blockchain-Backed)

A secure, anonymous, and verifiable student feedback system built with **Flask**, **MongoDB**, and **Hash-Based Blockchain** Technology. This system ensures that student feedback is tamper-proof while maintaining controlled anonymity, which can be revealed only by authorized personnel under specific conditions with audit logging.

## 🚀 Key Features

### 🔐 Security & Integrity
- **Blockchain Verification**: Every feedback submission is linked to the previous one via SHA-256 hashing. Any modification to past feedback invalidates the entire chain, detectable via the Admin Dashboard.
- **Controlled Anonymity**: Student identities are encrypted using Fernet (AES). Faculty and Admins cannot see who sent the feedback.
- **Identity Reveal Protocol**: Only the `Authority` role can decrypt a student's identity, and **every reveal is logged** in an immutable audit ledger with a mandatory reason.

### 👥 Role-Based Access Control
The system features four distinct roles:
1. **Student**: Can submit anonymous feedback for faculty.
2. **Faculty**: Can view feedback received for their courses.
3. **Admin**: Manages users (Faculty/Students), deletes feedback (soft delete), and monitors blockchain integrity.
4. **Authority**: A special oversight role that can audit feedback and reveal identities in cases of policy violations (e.g., harassment).

### 🎨 Modern UI/UX
- **Institutional Design**: A clean, light-first professional interface using a deep blue and teal color palette.
- **Responsive Layout**: Features a collapsible sidebar for easy navigation on all devices.
- **User-Friendly**: Clear visual indicators for blockchain status, audit logs, and feedback ratings.

---

## 🛠️ Technology Stack
- **Backend**: Python (Flask)
- **Database**: MongoDB (Local)
- **Frontend**: HTML5, CSS3, Bootstrap 5 (Custom "Institutional" Theme)
- **Cryptography**: `hashlib` (SHA-256), `cryptography` (Fernet)

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
*Note: On the first run, a `secret.key` file will be generated for encryption. Keep this file secure.*

### 4. Access the App
Open your browser and navigate to:
`http://127.0.0.1:5000`

---

## 👤 Default Credentials (for Demo)
The application creates default users if they don't exist:

| Role | Username | Password |
|------|----------|----------|
| **Admin** | `admin` | `admin123` |
| **Authority** | `authority` | `auth123` |

*You can create Student and Faculty accounts via the Admin Dashboard.*

---

## 📸 Screenshots

- **Login Page**: Secure entry point for all roles.
- **Student Dashboard**: Simple star rating and comment form.
- **Admin Dashboard**: System status indicators showing "Blockchain Valid/Invalid".
- **Authority Console**: Audit logs and identity reveal interface.

---

## 🛡️ License
This project is for educational and portfolio purposes.
