# 🔒 SecureAuth

SecureAuth is a **three-phase security platform** designed to provide **user authentication**, **secure password management with sharing**, and **file encryption & storage**.  
It ensures **end-to-end encryption** and provides a seamless, secure experience for managing sensitive data.

---

## 🚀 Features
- User authentication using a time-based one-time password (TOTP) system for third-party app logins
- Secure Password Vault with encryption
- Password sharing (with **browser extension support**)
- Encrypted File Vault for safe file storage
- AES + RSA hybrid cryptography for password & file security

---

## 📂 Project Phases

### **Phase 1 – Authenticator**
The **Authenticator** module provides secure **user registration and login**.  
- Users create accounts with email & password.  
- Passwords are stored using **bcrypt hashing**.  
- Public/private RSA key pairs are generated for each user.  
- After login, the Authenticator generates time-based one-time passwords (TOTP) for access to other connected apps. 

This phase ensures only **authenticated users** can access the Vaults.

---

### **Phase 2 – Password Vault & Sharing**
The **Password Vault** allows users to store, retrieve, and manage credentials securely.  
- Passwords are **AES-encrypted** before being stored in the database.  
- Decryption keys are derived from the user’s private key.  
- A clean dashboard shows saved credentials with auto-login support.

🔑 **Password Sharing**:
- Users can securely **share credentials** with other users.  
- Shared passwords are encrypted with an **AES session key**, which is wrapped with the **receiver’s RSA public key**.  
- The receiver decrypts it using their private key.  
- Sharing includes:
  - **Send & Receive shared credentials**  
  - **Revoke or delete shared credentials**  

🌐 **Browser Extension Support**:  
For seamless usage, a **browser extension** is integrated to auto-fill shared credentials, making secure collaboration easier.

---

### **Phase 3 – File Vault**
The **File Vault** provides secure file upload, encryption, and download.  
- Files are encrypted using **AES-GCM with PBKDF2-derived keys**.  
- Encrypted files are stored in the database.  
- To download, users must enter the correct encryption password.  
- Features:
  - Upload & Encrypt files
  - Decrypt & Download files
  - Delete stored files  

This ensures that sensitive documents remain confidential and accessible only with the right credentials.

---

## 🛠️ Tech Stack
- **Backend**: Python (Flask)  
- **Database**: MySQL (Workbench for schema design)  
- **Cryptography**: AES-GCM, RSA, PBKDF2, bcrypt  
- **Frontend**: HTML5, CSS3, Bootstrap 5, Glassmorphism design  
- **Browser Extension**: Integrated for password sharing auto-fill  

---

## ⚡ Setup & Run

1. Clone repository:
   ```bash
   git clone https://github.com/your-repo/SecureAuth.git
   cd SecureAuth
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure database in `app/db.py` and initialize schema via Workbench.

4. Run Flask app:
   ```bash
   flask run
   ```

5. Open in browser:
   ```
   http://127.0.0.1:5000
   ```

---

## 📌 Future Improvements
- Multi-factor authentication (MFA)  
- Cloud storage integration for File Vault  
- Secure file sharing  
- Browser extension enhancements (auto-save, sync)  
- Audit logs for password sharing  
