import os, uuid, io,base64
from datetime import datetime
from flask import (
    Blueprint, request, send_file, redirect,
    url_for, render_template, session, flash
)
from werkzeug.utils import secure_filename
from Crypto.Random import get_random_bytes
from app.utils.crypto_utils import encrypt_file, decrypt_file
from app.db import get_connection

bp = Blueprint("file", __name__)

UPLOAD_FOLDER = "uploads/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- Upload page (UI) ---
@bp.route("/vault/upload", methods=["GET"])
def upload_page():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("filevault/upload.html")


# --- Upload + Encrypt file ---
@bp.route("/vault/upload", methods=["POST"])
def upload_file():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    file = request.files["file"]
    password = request.form["password"]

    file_data = file.read()
    salt = get_random_bytes(16)
    encrypted = encrypt_file(file_data, password, salt)

    file_id = uuid.uuid4().hex 
    safe_name = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.bin")

    with open(file_path, "wb") as f:
        f.write(encrypted)

    # --- Save metadata in DB ---
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO Encrypted_Files (file_id, filename, encrypted_url, uploaded_by, encrypted_key, uploaded_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            file_id,
            safe_name,
            file_path,
            session.get("user_id"),
            base64.b64encode(salt).decode(),
            datetime.utcnow(),
        ),
    )
    conn.commit()
    cur.close()
    conn.close()

    flash("File uploaded and encrypted successfully!", "success")
    return redirect(url_for("file.list_files"))


# --- List user’s uploaded files ---
@bp.route("/vault/files", methods=["GET"])
def list_files():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT file_id, filename, uploaded_at
        FROM Encrypted_Files
        WHERE uploaded_by=%s
        ORDER BY uploaded_at DESC
        """,
        (session.get("user_id"),),
    )
    rows = cur.fetchall()
    files = [{"file_id": r[0], "filename": r[1], "uploaded_at": r[2]} for r in rows]
    cur.close()
    conn.close()

    return render_template("filevault/files.html", files=files)


# --- Decrypt + Download file ---
@bp.route("/vault/download/<file_id>", methods=["POST"])
def download_file(file_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    password = request.form["password"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT filename, encrypted_url, encrypted_key
        FROM Encrypted_Files
        WHERE file_id=%s AND uploaded_by=%s
        """,
        (file_id, session.get("user_id")),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"error": "File not found or access denied"}, 404

    file_name, file_path, salt_b64 = row   # <-- path, not blob
    salt = base64.b64decode(salt_b64)

    # Read encrypted bytes from file
    with open(file_path, "rb") as f:
        enc_data = f.read()

    try:
        decrypted = decrypt_file(enc_data, password, salt)
        return send_file(
            io.BytesIO(decrypted),
            as_attachment=True,
            download_name=file_name
        )
    except Exception:
        return {"error": "Wrong password or file corrupted"}, 400


@bp.route("/delete/<file_id>", methods=["POST"])
def delete_file(file_id):
    if "user_id" not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for("auth.login"))

    db = get_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM Encrypted_files WHERE file_id = %s AND uploaded_by = %s", (file_id, session["user_id"]))
    db.commit()
    cursor.close()
    db.close()

    flash("File deleted successfully.", "success")
    return redirect(url_for("file.list_files"))