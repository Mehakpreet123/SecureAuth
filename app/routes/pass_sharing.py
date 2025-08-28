from flask import Blueprint, request, session, redirect, url_for, jsonify,render_template,flash
from app.db import get_connection
import uuid, base64, json
from datetime import datetime, timedelta
from app.utils.crypto_utils import (
    aesgcm_encrypt, aesgcm_decrypt, rsa_wrap_key, rsa_unwrap_key,
    load_public_key, load_private_key_encrypted, pack_share_token, unpack_share_token,encrypt_password,decrypt_password
    ,load_key,load_private_key
)
from app.utils.auth_utils import validate_token
from app.utils.security import derive_key_from_password

bp = Blueprint("sharing", __name__)

# ---------------- CREATE SHARE ----------------
@bp.route("/share/<vault_id>", methods=["POST"])
def create_share(vault_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    receiver_username = request.form["receiver"]
    days = int(request.form.get("days", 3))

    db = get_connection()
    cursor = db.cursor(dictionary=True)

    # Get sender’s credential
    cursor.execute("SELECT * FROM password_vault WHERE vault_id=%s AND user_id=%s",
                   (vault_id, session["user_id"]))
    cred = cursor.fetchone()
    if not cred:
        return jsonify({"error": "not found"}), 404

    # Get receiver public key
    cursor.execute("SELECT u.user_id, k.public_key_pem FROM users u "
                   "JOIN user_keys k ON u.user_id=k.user_id "
                   "WHERE u.username=%s", (receiver_username,))
    recv = cursor.fetchone()
    if not recv:
        return jsonify({"error": "receiver not found"}), 404

    # Decrypt sender’s password
    from app.utils.crypto_utils import decrypt_password, load_key
    plaintext = decrypt_password(cred["password_enc"], load_key()).encode()

    # Encrypt with AES
    aes_key, nonce, ct = aesgcm_encrypt(plaintext)

    # Wrap AES key with receiver’s pubkey
    pub = load_public_key(recv["public_key_pem"])
    wrapped = rsa_wrap_key(pub, aes_key)

    token = pack_share_token(wrapped, nonce, ct)

    share_id = uuid.uuid4().hex
    cursor.execute("""
        INSERT INTO vault_sharing 
        (share_id, vault_id, sender_id, receiver_id, access_token, expires_at, status) 
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (share_id, vault_id, session["user_id"], recv["user_id"], token,
          datetime.utcnow() + timedelta(days=days), "active"))
    db.commit()
    cursor.close()
    return jsonify({"share_id": share_id, "status": "active"})

# ---------------- CONSUME SHARE ----------------
@bp.route("/share/consume/<share_id>", methods=["POST"])
def consume_share(share_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    login_pw = request.form["login_password"]
    db = get_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vault_sharing WHERE share_id=%s AND receiver_id=%s",
                   (share_id, session["user_id"]))
    share = cursor.fetchone()
    if not share:
        return jsonify({"error": "not found"}), 404

    if share["status"] != "active":
        return jsonify({"error": "inactive"}), 403

    # Get receiver private key
    cursor.execute("SELECT * FROM user_keys WHERE user_id=%s", (session["user_id"],))
    keys = cursor.fetchone()
    cursor.close()

    salt = base64.b64decode(keys["salt"].encode())
    passkey = derive_key_from_password(login_pw, salt)
    priv = load_private_key_encrypted(keys["private_key_pem_enc"], passkey)

    wrapped, nonce, ct = unpack_share_token(share["access_token"])
    aes_key = rsa_unwrap_key(priv, wrapped)
    plaintext = aesgcm_decrypt(aes_key, nonce, ct).decode()

    return jsonify({"password": plaintext})

@bp.route("/page/<vault_id>", methods=["GET", "POST"])
def share_page(vault_id):
    if "user_id" not in session:
        print("❌ No active session, redirecting to login")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        receiver = request.form["receiver"].strip()
        days = int(request.form.get("days", 3))

        print("\n=== 🔑 SHARE DEBUG START ===")
        print("Vault ID from URL:", vault_id)
        print("Current logged-in user (sender):", session["user_id"])
        print("Receiver input (email):", receiver)
        print("Days until expiry:", days)

        db = get_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # 1. Get sender’s vault item
            cursor.execute("""
                SELECT * FROM password_vault 
                WHERE vault_id=%s AND user_id=%s
            """, (vault_id, session["user_id"]))
            cred = cursor.fetchone()
            print("Fetched Vault Item:", cred)

            if not cred:
                flash("Vault item not found", "error")
                print("❌ Vault item not found for this user")
                return redirect(url_for("vault.dashboard"))

            # 2. Get receiver public key
            cursor.execute("""
                SELECT u.user_id, k.public_key_pem 
                FROM users u 
                JOIN user_keys k ON u.user_id=k.user_id 
                WHERE u.email=%s
            """, (receiver,))
            recv = cursor.fetchone()
            print("Fetched Receiver:", recv)

            if not recv:
                flash("Receiver not found", "error")
                print("❌ Receiver not found in users+user_keys")
                return redirect(url_for("vault.dashboard"))

            # 3. Decrypt sender’s password
            plaintext = decrypt_password(
                cred["password_enc"], 
                load_key()
            ).encode()
            print("Decrypted plaintext length:", len(plaintext))

            # 4. Encrypt with AES session key
            aes_key, nonce, ct = aesgcm_encrypt(plaintext)
            print("Generated AES key length:", len(aes_key))
            print("Nonce length:", len(nonce))
            print("Ciphertext length:", len(ct))

            # 5. Wrap AES key with receiver’s public RSA key
            pub = load_public_key(recv["public_key_pem"])
            wrapped = rsa_wrap_key(pub, aes_key)
            print("Wrapped AES key length:", len(wrapped))

            # 6. Pack into JSON token
            token = pack_share_token(wrapped, nonce, ct)
            print("Packed token length:", len(token))

            # 7. Insert into password_sharing table
            share_id = uuid.uuid4().hex  # 32 chars
            print("Generated Share ID:", share_id)

            cursor.execute("""
                INSERT INTO password_sharing
                (share_id, vault_id, sender_id, receiver_id, access_token, shared_at, expires_at, status)
                VALUES (%s,%s,%s,%s,%s,NOW(),%s,%s)
            """, (
                share_id,
                vault_id,
                session["user_id"],
                recv["user_id"],
                token,
                datetime.utcnow() + timedelta(days=days),
                "active"
            ))
            db.commit()

            print("✅ Inserted row into password_sharing")

            flash("Password shared successfully!", "success")

        except Exception as e:
            db.rollback()
            print("❌ Error inserting into password_sharing:", e)
            flash("Error sharing password: " + str(e), "error")

        finally:
            cursor.close()
            db.close()
            print("=== 🔑 SHARE DEBUG END ===\n")

        return redirect(url_for("vault.dashboard"))

    print("⚠️ GET request received for share_page")
    return render_template("sharing/share.html", vault_id=vault_id)


from cryptography.hazmat.primitives import serialization

@bp.route("/shared")
def shared_vaults():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch shared credentials for this user
    cursor.execute("""
        SELECT s.share_id, s.access_token, v.title, v.username, v.website, v.notes,
               u.username AS sender_name
        FROM password_sharing s
        JOIN password_vault v ON s.vault_id = v.vault_id
        JOIN users u ON s.sender_id = u.user_id
        WHERE s.receiver_id=%s AND s.status='active'
    """, (session["user_id"],))

    shared_items = cursor.fetchall()
    cursor.close()
    db.close()

    processed = []
    for item in shared_items:
        try:
            # Load receiver’s unlocked private key from session
            priv = serialization.load_pem_private_key(
                session["private_key"].encode(),
                password=None
            )

            # Decrypt shared token
            password = unpack_share_token(item["access_token"], priv)

            processed.append({
                "share_id": item["share_id"],
                "title": item["title"],
                "username": item["username"],
                "website": item["website"],
                "notes": item["notes"],
                "sender_name": item["sender_name"],
                "password": password   # keep backend-only for autologin
            })

        except Exception as e:
            print("❌ Error decrypting shared item:", e)

    # Render template WITHOUT exposing password
    return render_template("sharing/shared.html", shared_items=processed)


@bp.route("/shared/delete/<share_id>", methods=["DELETE"])
def delete_shared(share_id):
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    user_id = session["user_id"]

    db = get_connection()
    cursor = db.cursor()

    try:
        cursor.execute("""
            DELETE FROM password_sharing
            WHERE share_id=%s AND receiver_id=%s
        """, (share_id, user_id))
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": "No entry found or not authorized"}), 404

        return jsonify({"success": True, "message": "Shared credential deleted successfully"})
    except Exception as e:
        print("❌ Delete error:", e)
        return jsonify({"success": False, "error": "Server error"}), 500
    finally:
        cursor.close()
        db.close()


@bp.route("/shared/sent")
def shared_sent():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch credentials shared BY this user
    cursor.execute("""
        SELECT s.share_id, s.access_token, v.title, v.username, v.website, v.notes,
               u.username AS receiver_name, s.status, s.expires_at
        FROM password_sharing s
        JOIN password_vault v ON s.vault_id = v.vault_id
        JOIN users u ON s.receiver_id = u.user_id
        WHERE s.sender_id=%s
    """, (session["user_id"],))

    shared_items = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("sharing/shared_sent.html", shared_items=shared_items)


@bp.route("/shared/revoke/<share_id>", methods=["POST"])
def revoke_share(share_id):
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    db = get_connection()
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE password_sharing
            SET status='revoked'
            WHERE share_id=%s AND sender_id=%s
        """, (share_id, session["user_id"]))
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": "No entry found or not authorized"}), 404

        return jsonify({"success": True, "message": "Share revoked successfully"})
    except Exception as e:
        print("❌ Revoke error:", e)
        return jsonify({"success": False, "error": "Server error"}), 500
    finally:
        cursor.close()
        db.close()
