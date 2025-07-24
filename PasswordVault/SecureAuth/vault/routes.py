from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from .vault_core import PasswordVault

vault_bp = Blueprint("vault", __name__, template_folder="../templates", url_prefix="/vault")
_vaults: dict[str, PasswordVault] = {}

def _vault() -> PasswordVault:
    uid = session["user_id"]
    return _vaults.setdefault(uid, PasswordVault(master_password=uid))

@vault_bp.route("/")
def dashboard():
    services = list(_vault().store[session["user_id"]].keys())
    return render_template("vault.html", services=services)

@vault_bp.route("/add", methods=["POST"])
def add():
    svc = request.form["service"].strip()
    pwd = request.form.get("password") or _vault().new_password()
    _vault().add(session["user_id"], svc, pwd)
    flash("Credential saved", "success")
    return redirect(url_for("vault.dashboard"))

@vault_bp.route("/password/<service>")
def show_password(service):
    pwd = _vault().get(session["user_id"], service)
    if pwd is None:
        flash("Service not found", "danger")
        return redirect(url_for("vault.dashboard"))
    return jsonify({"password": pwd})

@vault_bp.route("/search")
def search():
    q = request.args.get("q", "")
    return jsonify({"services": _vault().search(q)})
