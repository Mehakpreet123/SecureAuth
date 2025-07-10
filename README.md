# 🔐 SecureAuth – DSA-Powered Web-Based TOTP Authenticator

SecureAuth is a full-stack, browser-based authenticator application that allows users to securely manage their Two-Factor Authentication (2FA) tokens using Time-Based One-Time Passwords (TOTP). What makes SecureAuth unique is its **core foundation in Data Structures and Algorithms (DSA)** — every feature, from OTP handling to credential management, is designed using efficient and scalable DSA techniques.

---

## 📌 Project Description

SecureAuth replicates the functionality of authenticators like Google Authenticator but is fully web-based. It supports scanning QR codes, entering base32 secrets, and generating valid 6-digit OTPs that update every 30 seconds.

The backend logic, OTP storage, rate-limiting, and history tracking are all implemented using appropriate **DSA components** — making it both secure and educational for demonstrating how DSA powers real-world systems.

---

## ✅ Key Features

- 🔐 User Registration and Login
- 📷 QR Code Scanning (In-Browser)
- 🔑 Manual Entry of base32 secrets
- 🕒 TOTP-based 6-digit OTP generation every 30 seconds
- 📋 Dashboard to manage services and codes
- 🧭 Auto-suggestion of service names

---

## 🧱 Tech Stack

### Frontend:
- HTML5
- CSS3
- JavaScript

### Backend:
- Python with Flask
- `pyotp` for RFC-compliant TOTP generation
- `Werkzeug` for password hashing

---

## 🔁 Application Workflow

1. User visits SecureAuth and signs up or logs in.
2. On the dashboard, user clicks “Add New Entry”.
3. User either:
   - Scans a QR code from a third-party service, or
   - Manually enters the base32 secret and service name.
4. SecureAuth extracts and stores the TOTP secret securely.
5. A 6-digit OTP is generated every 30 seconds using TOTP logic.
6. The user can copy the OTP and use it for two-factor authentication.
7. System manages OTP expiry, logs activity, and ensures rate limits.

---

## 🧠 DSA Logic & Algorithms Used

| Feature | DSA/Algorithm Used | Purpose |
|--------|---------------------|---------|
| **User Authentication** | Hash Map (Dictionary) | Fast username-password mapping for login/signup |
| **OTP Generation** | TOTP (RFC 6238), Time-based HMAC | Secure, rolling one-time passwords |
| **Secret Versioning** | Stack | Push/pop previous secrets, rollback on update |
| **Brute Force Prevention** | Queue + Sliding Window | Track login attempts per time interval |
| **Access Logs** | Deque (Double-ended Queue) | Log recent user activities efficiently |
| **Service Auto-Suggest** | Trie | Fast prefix-based service name suggestions |
| **Secret Validation** | Regex + String Matching | Validate base32 formats from QR or manual input |
| **OTP Expiry Management** | Circular Queue / Min-Heap | Manage rolling 30s windows and expired codes |

---

## 🔮 Future Scope

The upcoming release of SecureAuth will introduce a **Vault Module**, making it a full-fledged security suite. Features of the Vault include:

### 🔐 Secure Password Vault (Planned)

- Store and retrieve passwords for multiple services
- Encrypt passwords using strong symmetric encryption (e.g., AES)
- Generate random strong passwords with constraints
- Version control for passwords using a stack
- Search through stored credentials using Trie
- Access logs for viewing history of access/edit
- Optional PIN or biometric-based unlock (browser-supported)

**DSA Used in Vault Module:**

| Feature | DSA Used | Description |
|--------|----------|-------------|
| Password History | Stack | Undo/rollback support for password updates |
| Credential Lookup | Trie | Fast search by service/domain |
| Secure Mapping | Hash Map | `user_id → {service → credentials}` |
| Password Strength Check | String Analysis | Pattern matching, dictionary lookups |
| Activity Tracking | Deque | Logging of all interactions with vault |

---

## 📌 How to Run Locally

1. Clone the repository:
git clone https://github.com/Mehakpreet123/secureauth.git
2. Navigate to the project folder:
cd SecureAuth
3. Install dependencies:
pip install -r requirements.txt
4. Run the application:
python app.py
5. Open your browser and go to:
http://localhost:5000
