from flask import Flask
from flask_cors import CORS  # ✅ Import this
from .routes import mainpage
from config import Config

db = None

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY  # Optional if already in Config

    # ✅ Enable CORS with credentials
    CORS(app, supports_credentials=True)

    from .routes import auth, vault,authenticator,pass_sharing
    app.register_blueprint(auth.bp)
    app.register_blueprint(mainpage.bp)
    app.register_blueprint(vault.bp)
    app.register_blueprint(authenticator.authenticator_bp)
    app.register_blueprint(pass_sharing.bp)



    return app
