import os
from flask import Flask, redirect, url_for, session
from vault.routes import vault_bp            # your existing blueprint

# ──────────────────────────────────────────────────────────────
# Flask factory
# ──────────────────────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Core config (use env var in production)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", os.urandom(24))

    # Register the vault blueprint
    app.register_blueprint(vault_bp)

    # Ensure a default user_id in every request
    @app.before_request
    def set_guest_user():
        session.setdefault("user_id", "guest")

    # Root path → vault dashboard
    @app.route("/")
    def index():
        return redirect(url_for("vault.html"))

    return app


# ──────────────────────────────────────────────────────────────
# Run locally
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
