from flask import Blueprint, render_template, request, redirect, flash, session, url_for, jsonify
from app.db import get_connection
from app.utils.security import hash_password, verify_password
import uuid
from app.utils.auth_utils import generate_token, check_password
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

bp = Blueprint("auth", __name__)

# ==========================
# 🔑 SIGNUP
# ==========================
@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            flash("Username exists. Choose other")
            cursor.close()
            conn.close()
            return redirect("/signup")
        
        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            flash("Email already registered.")
            cursor.close()
            conn.close()
            return redirect("/signup")

        # Create user
        hashed_pw = hash_password(password)
        user_id = str(uuid.uuid4()).replace("-", "")

        cursor.execute(
            "INSERT INTO users (user_id, username, email, password_hash) VALUES (%s, %s, %s, %s)",
            (user_id, username, email, hashed_pw)
        )
        conn.commit()

        # Generate RSA keypair
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        private_pem_enc = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password.encode())
        ).decode()

        cursor.execute("""
            INSERT INTO user_keys (key_id, user_id, public_key_pem, private_key_pem_enc, salt)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            str(uuid.uuid4()),
            user_id,
            public_pem,
            private_pem_enc,
            ""
        ))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Signup successful. Please login.")
        return redirect("/login")

    return render_template("signup.html")

# ==========================
# 🔑 LOGIN
# ==========================
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user or not verify_password(password, user["password_hash"]):
            cursor.close()
            conn.close()
            flash("Invalid credentials.")
            return redirect("/login")

        cursor.execute("SELECT private_key_pem_enc FROM user_keys WHERE user_id=%s", (user["user_id"],))
        key_row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not key_row:
            flash("No private key found for this user.")
            return redirect("/login")

        try:
            priv = serialization.load_pem_private_key(
                key_row["private_key_pem_enc"].encode(),
                password=password.encode(),
                backend=default_backend()
            )
            priv_pem_unenc = priv.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            # ✅ Set session correctly
            session.clear()  # Clear previous session just in case
            session["user_id"] = user["user_id"]
            session["email"] = email
            session["private_key"] = priv_pem_unenc.decode()
            print(session['email'])

            return redirect(url_for("mainpage.main_dashboard"))

        except Exception as e:
            print("❌ Error unlocking private key:", e)
            flash("Error unlocking private key. Please check your password.")
            return redirect("/login")

    return render_template("login.html")

# ==========================
# 🔑 API LOGIN
# ==========================
# @bp.route('/api/login', methods=['POST'])
# def api_login():
#     data = request.json
#     email = data.get('email')
#     password = data.get('password')

#     db = get_connection()
#     cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
#     user = cursor.fetchone()
#     cursor.close()

#     if not user or not check_password(password, user['password_hash']):
#         return jsonify({"success": False, "error": "Invalid credentials"}), 401

#     # ✅ Optional: set session for browser login
#     session.clear()
#     session["user_id"] = user["user_id"]
#     session['email'] = user['email']
 

#     token = generate_token(user['user_id'])
#     return jsonify({"success": True, "token": token})


@bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    db = get_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user or not check_password(password, user['password_hash']):
        cursor.close()
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    cursor.execute("SELECT private_key_pem_enc FROM user_keys WHERE user_id=%s", (user["user_id"],))
    key_row = cursor.fetchone()
    cursor.close()
    db.close()

    if not key_row:
        return jsonify({"success": False, "error": "No private key found"}), 500

    try:
        # Unlock private key with user's password
        priv = serialization.load_pem_private_key(
            key_row["private_key_pem_enc"].encode(),
            password=password.encode(),
            backend=default_backend()
        )
        priv_pem_unenc = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # ✅ Store in session for later decryption
        session.clear()
        session["user_id"] = user["user_id"]
        session["email"] = user["email"]
        session["private_key"] = priv_pem_unenc.decode()

        token = generate_token(user['user_id'])
        return jsonify({"success": True, "token": token})

    except Exception as e:
        print("❌ API login error unlocking private key:", e)
        return jsonify({"success": False, "error": "Error unlocking private key"}), 401


# ==========================
# 🔑 LOGOUT
# ==========================
@bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
