from flask import Flask, render_template, request, redirect, session,url_for,send_file, flash, get_flashed_messages
from dsa.hashmap import HashMap, User
import hashlib
import os
from vault.filevault import encrypt_file, decrypt_file
import threading
import time
import json
app = Flask(__name__)
app.secret_key = "supersecretkey"
users = HashMap()


USER_FILE = 'users.json'

if os.path.exists(USER_FILE):
    with open(USER_FILE, 'r') as f:
        raw_users = json.load(f)
        users = {u: User(u, p) for u, p in raw_users.items()}
else:
    users = {}


UPLOAD_FOLDER = 'vault_storage'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            flash("⚠️ Username already exists!", "warning")
        else:
            # ✅ Hash the password before storing
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            users[username] = User(username, password_hash)

            # 💾 Save users to JSON file
            with open(USER_FILE, 'w') as f:
                json.dump({u: user.password_hash for u, user in users.items()}, f)

            flash("✅ Signup successful! Please login.", "success")
            return redirect("/login")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = users.get(username)

        if user and user.password_hash == hashlib.sha256(password.encode()).hexdigest():
            session["user"] = username
            return redirect("/dashboard")
        else:
            flash("❌ Invalid username or password", "danger")
            return redirect("/login")
    return render_template("login.html")

@app.route("/")
def index():
    return redirect("/signup")

@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect("/login")
    
    files = os.listdir(UPLOAD_FOLDER)
    return render_template("dashboard.html", user=session["user"], files=files)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    password = request.form.get('password')

    if not file or file.filename == '':
        flash("⚠️ No file selected.", "warning")
        return redirect(url_for('dashboard'))

    if not password:
        flash("⚠️ Password is required for encryption.", "warning")
        return redirect(url_for('dashboard'))

    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        encrypted_path = encrypt_file(filepath, password)

        os.remove(filepath)  # delete original file

        flash(f"✅ File encrypted and saved as '{os.path.basename(encrypted_path)}'!", "success")
    except Exception as e:
        flash(f"❌ Error encrypting file: {str(e)}", "danger")

    return redirect(url_for('dashboard'))



def delayed_delete(filepath, delay=5):
    def delete():
        time.sleep(delay)
        try:
            os.remove(filepath)
            print(f"✅ Deleted: {filepath}")
        except Exception as e:
            print(f"❌ Could not delete {filepath}: {e}")
    threading.Thread(target=delete).start()

@app.route('/decrypt', methods=['POST'])
def decrypt_route():
    filename = request.form['filename']
    password = request.form['password']

    filepath = os.path.join('vault_storage', filename)

    if not os.path.exists(filepath):
        flash(f"❌ File not found: {filepath}", "danger")
        return redirect(url_for('dashboard'))

    try:
        decrypted_path = decrypt_file(filepath, password)

        # Send file to client
        response = send_file(decrypted_path, as_attachment=True)

        # Schedule deletion after 5 seconds
        delayed_delete(decrypted_path, delay=5)

        return response

    except Exception as e:
        flash(f"❌ Wrong password or failed to decrypt: {str(e)}", "danger")
        return redirect(url_for('dashboard'))








if __name__ == "__main__":
    app.run(debug=True)

