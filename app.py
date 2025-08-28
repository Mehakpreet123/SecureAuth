import os
from flask import Flask, render_template, request, redirect, url_for, send_file
from vault.file_encryption import generate_key, encrypt_file, decrypt_file
from vault.storage import save_file_metadata, get_all_files

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
DECRYPTED_FOLDER = "decrypted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)

generate_key()  # ensure AES key exists

@app.route("/", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            encpath = os.path.join(UPLOAD_FOLDER, f"{file.filename}.enc")
            file.save(filepath)
            encrypt_file(filepath, encpath)
            os.remove(filepath)  # delete original unencrypted
            save_file_metadata(file.filename)
            return redirect(url_for("dashboard"))
    files = get_all_files()
    return render_template("dashboard.html", files=files)

@app.route("/decrypt/<filename>")
def decrypt(filename):
    encpath = os.path.join(UPLOAD_FOLDER, f"{filename}.enc")
    decpath = os.path.join(DECRYPTED_FOLDER, filename)
    decrypt_file(encpath, decpath)
    return send_file(decpath, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
