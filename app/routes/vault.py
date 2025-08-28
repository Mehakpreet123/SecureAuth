from flask import Blueprint, render_template, request, redirect, session, url_for,jsonify
from app.utils.crypto_utils import load_key, encrypt_password, decrypt_password,unpack_share_token,load_private_key
from app.db import get_connection
import uuid
from app.utils.auth_utils import validate_token
from cryptography.hazmat.primitives import serialization

bp = Blueprint('vault', __name__)

@bp.route('/vault')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT vault_id, title, username, website, created_at, updated_at
        FROM password_vault
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (session['user_id'],))
    
    creds = cursor.fetchall()
    cursor.close()

    return render_template('vault/dashboard.html', credentials=creds)


@bp.route("/vault/add", methods=["GET", "POST"])
def add_credential():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == "POST":
        title = request.form["title"]
        username = request.form["username"]
        password = request.form["password"]
        website = request.form["website"]
        notes = request.form["notes"]
        user_id = session.get("user_id")

        key = load_key()
        encrypted_password = encrypt_password(password, key)

        db = get_connection()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO password_vault (vault_id, user_id, title, username, password_enc, website, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (str(uuid.uuid4()).replace("-",""), user_id, title, username, encrypted_password, website, notes))
        db.commit()
        cursor.close()
        return redirect(url_for('vault.dashboard'))
    
    return render_template("vault/add.html")

@bp.route("/vault/view/<vault_id>")
def view_credential(vault_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT vault_id, title, username, password_enc, website, notes, created_at, updated_at
        FROM password_vault
        WHERE vault_id = %s AND user_id = %s
    """, (vault_id, session['user_id']))
    
    cred = cursor.fetchone()
    cursor.close()

    if not cred:
        return redirect(url_for('vault.dashboard'))  # or a custom 404 page

    key = load_key()
    decrypted_password = decrypt_password(cred["password_enc"], key)

    return render_template("vault/view.html", cred=cred, decrypted_password=decrypted_password)

@bp.route("/vault/edit/<vault_id>", methods=["GET", "POST"])
def edit_credential(vault_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        title = request.form["title"]
        username = request.form["username"]
        password = request.form["password"]
        website = request.form["website"]
        notes = request.form["notes"]

        key = load_key()
        encrypted_password = encrypt_password(password, key)

        cursor.execute("""
            UPDATE password_vault
            SET title=%s, username=%s, password_enc=%s, website=%s, notes=%s, updated_at=NOW()
            WHERE vault_id=%s AND user_id=%s
        """, (title, username, encrypted_password, website, notes, vault_id, session['user_id']))
        db.commit()
        cursor.close()

        return redirect(url_for('vault.dashboard'))

    cursor.execute("""
        SELECT * FROM password_vault
        WHERE vault_id=%s AND user_id=%s
    """, (vault_id, session['user_id']))
    cred = cursor.fetchone()
    cursor.close()

    if not cred:
        return redirect(url_for('vault.dashboard'))

    key = load_key()
    decrypted_password = decrypt_password(cred["password_enc"], key)
    return render_template("vault/edit.html", cred=cred, decrypted_password=decrypted_password)


@bp.route("/vault/delete/<vault_id>", methods=["POST"])
def delete_credential(vault_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_connection()
    cursor = db.cursor()
    cursor.execute("""
        DELETE FROM password_vault WHERE vault_id=%s AND user_id=%s
    """, (vault_id, session['user_id']))
    db.commit()
    cursor.close()
    return redirect(url_for('vault.dashboard'))



# def autofill():
#     data = request.json
#     domain = data.get("domain")
#     token = request.headers.get("Authorization", "").replace("Bearer ", "")

#     # Validate token → get user_id
#     user_id = validate_token(token)
#     if not user_id:
#         return jsonify({"success": False, "error": "Unauthorized"}), 401

#     db = get_connection()
#     cursor = db.cursor(dictionary=True)
#     cursor.execute("""
#         SELECT username, password_enc FROM password_vault
#         WHERE website LIKE %s AND user_id = %s
#         LIMIT 1
#     """, (f"%{domain}%", user_id))
#     row = cursor.fetchone()
#     cursor.close()

#     if not row:
#         return jsonify({"success": False, "error": "No match"}), 404

#     decrypted = decrypt_password(row["password_enc"], load_key())
#     return jsonify({"success": True, "data": {"username": row["username"], "password": decrypted}})


# @bp.route("/vault/api/autofill", methods=["POST"])
# def autofill():
#     data = request.get_json(silent=True) or {}
#     domain = data.get("domain")
#     token = request.headers.get("Authorization", "").replace("Bearer ", "")

#     # Validate token → get user_id
#     user_id = validate_token(token)
#     if not user_id:
#         return jsonify({"success": False, "error": "Unauthorized"}), 401

#     db = get_connection()
#     cursor = db.cursor(dictionary=True)

#     # 1️⃣ Try to fetch from user’s own vault
#     cursor.execute("""
#         SELECT username, password_enc, 'own' AS source
#         FROM password_vault
#         WHERE website LIKE %s AND user_id = %s
#         LIMIT 1
#     """, (f"%{domain}%", user_id))
#     row = cursor.fetchone()

#     # 2️⃣ If not found, try shared vaults
#     if not row:
#         cursor.execute("""
#             SELECT v.username, s.access_token, 'shared' AS source
#             FROM password_sharing s
#             JOIN password_vault v ON s.vault_id = v.vault_id
#             WHERE v.website LIKE %s AND s.receiver_id = %s AND s.status='active'
#             LIMIT 1
#         """, (f"%{domain}%", user_id))
#         row = cursor.fetchone()

#     cursor.close()
#     db.close()

#     if not row:
#         return jsonify({"success": False, "error": "No match"}), 404

#     # 3️⃣ Decrypt
#     if row["source"] == "own":
#         decrypted = decrypt_password(row["password_enc"], load_key())

#     elif row["source"] == "shared":
#         try:
#             # Load receiver’s private key from session (unlocked at login)
#             priv_pem = session.get("private_key")
#             if not priv_pem:
#                 return jsonify({"success": False, "error": "No private key in session"}), 403

#             from app.utils.crypto_utils import load_private_key, unpack_share_token
#             priv = load_private_key(priv_pem, password=None)
#             decrypted = unpack_share_token(row["access_token"], priv)

#         except Exception as e:
#             print("❌ Autofill shared decrypt error:", e)
#             return jsonify({"success": False, "error": "Decrypt failed"}), 500

#     # 4️⃣ Return only for background autofill, not UI display
#     return jsonify({
#         "success": True,
#         "data": {
#             "username": row["username"],
#             "password": decrypted
#         }
#     })


@bp.route("/vault/api/autofill", methods=["POST"])
def autofill():
    data = request.get_json(silent=True) or {}
    domain = data.get("domain")
    login_password = data.get("password")  # needed for shared password decryption

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = validate_token(token)
    if not user_id:
        return jsonify({"success": False, "error": "Invalid or expired token"}), 401

    db = get_connection()
    cursor = db.cursor(dictionary=True)

    # 1️⃣ Try user’s own vault
    cursor.execute("""
        SELECT username, password_enc, 'own' AS source
        FROM password_vault
        WHERE website LIKE %s AND user_id = %s
        LIMIT 1
    """, (f"%{domain}%", user_id))
    row = cursor.fetchone()

    # 2️⃣ If not found, try shared vaults
    if not row:
        cursor.execute("""
            SELECT v.username, s.access_token, 'shared' AS source
            FROM password_sharing s
            JOIN password_vault v ON s.vault_id = v.vault_id
            WHERE v.website LIKE %s AND s.receiver_id = %s AND s.status='active'
            LIMIT 1
        """, (f"%{domain}%", user_id))
        row = cursor.fetchone()

    if not row:
        cursor.close()
        db.close()
        return jsonify({"success": False, "error": "No match"}), 404

    # 3️⃣ Decrypt password
    try:
        if row["source"] == "own":
            decrypted = decrypt_password(row["password_enc"], load_key())

        elif row["source"] == "shared":
            try:
                if not login_password:
                    return jsonify({"success": False, "error": "Login password required"}), 403

                cursor.execute("SELECT private_key_pem_enc FROM user_keys WHERE user_id=%s", (user_id,))
                key_row = cursor.fetchone()
                if not key_row:
                    print("❌ No private key found for user:", user_id)
                    return jsonify({"success": False, "error": "No private key found"}), 500

                private_key_pem_enc = key_row["private_key_pem_enc"]
                print("🔑 Private key fetched, length:", len(private_key_pem_enc))
                priv = load_private_key(private_key_pem_enc, login_password)
                print("🔑 Private key loaded successfully")
                decrypted = unpack_share_token(row["access_token"], priv)
                print("🔓 Shared password decrypted successfully")

            except Exception as e:
                print("❌ Autofill decrypt error (shared):", e)
                return jsonify({"success": False, "error": f"Decrypt failed: {str(e)}"}), 500

    except Exception as e:
        print("❌ Autofill decrypt error (shared):", e)
        return jsonify({"success": False, "error": f"Decrypt failed: {str(e)}"}), 500


    cursor.close()
    db.close()

    return jsonify({
        "success": True,
        "data": {
            "username": row["username"],
            "password": decrypted
        }
    })