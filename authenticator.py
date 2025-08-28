import pyotp
import uuid
from flask import Blueprint, request, render_template, redirect, url_for,session,flash
from app.db import get_connection
from .otp_manager import add_otp_entry, generate_otp, ingest_input

authenticator_bp = Blueprint('authenticator', __name__)

# -----------------------------
# Add a 3rd-party OTP secret (URI or raw secret)
# -----------------------------


@authenticator_bp.route("/authenticator/add_3rdparty", methods=["GET", "POST"])
def add_third_party():
    user_id = session.get("user_id")
    if not user_id:
        return "Unauthorized", 401

    if request.method == "POST":
        uri_or_secret = request.form.get("input_value", "").strip()
        label = request.form.get("label", "").strip()

        try:
            # Parse URI or raw secret input
            parsed_label, secret = ingest_input(uri_or_secret, fallback_label=label or None)
            db = get_connection()
            cursor = db.cursor(dictionary=True)

            # ✅ Check if the secret already exists for the same user
            cursor.execute("""
                SELECT * FROM otp_secrets 
                WHERE secret_key = %s AND assigned_to = %s
            """, (secret, user_id))
            existing = cursor.fetchone()

            if existing:
                error = "This OTP already exists in your account."
                return render_template("authenticator/add_third_party.html", error=error)

            # ✅ Insert new OTP
            add_otp_entry(parsed_label, secret, user_id, db)
            return redirect(url_for("authenticator.view_otps"))

        except Exception as e:
            return render_template("authenticator/add_third_party.html", error=str(e))

    return render_template("authenticator/add_third_party.html")



# -----------------------------
# Show all current OTPs from DB
# -----------------------------
@authenticator_bp.route("/authenticator/view_otps")
def view_otps():
    db = get_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT otp_secret_id,label, secret_key FROM OTP_Secrets
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()

    current_otps = [
        {
            "otp_secret_id": row["otp_secret_id"],
            "label": row["label"],
            "otp": generate_otp(row["secret_key"])
        }
        for row in rows
    ]

    return render_template("authenticator/list_otps.html", otps=current_otps)

@authenticator_bp.route('/authenticator/delete/<otp_id>', methods=['POST'])
def delete_otp(otp_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("You must be logged in to perform this action.")
        return redirect(url_for('auth.login'))

    conn = get_connection()
    cursor = conn.cursor()

    # Ensure OTP belongs to the user
    cursor.execute("DELETE FROM otp_secrets WHERE otp_secret_id = %s AND assigned_to = %s", (otp_id, user_id))
    conn.commit()

    cursor.close()
    conn.close()

    flash("OTP deleted successfully.")
    return redirect(url_for('authenticator.view_otps'))  # Adjust as needed

from flask import jsonify

@authenticator_bp.route("/authenticator/otps/json")
def get_otps_json():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify([])

    db = get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT otp_secret_id, label, secret_key FROM OTP_Secrets
        WHERE assigned_to = %s
        ORDER BY created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify([
        {
            "otp_secret_id": row["otp_secret_id"],
            "label": row["label"],
            "otp": generate_otp(row["secret_key"])
        }
        for row in rows
    ])

