from flask import Blueprint, render_template,session,redirect,url_for
bp = Blueprint('mainpage', __name__)

@bp.route('/')
def home():
    return render_template("home.html")  # renders the template file

# @bp.route('/main')
# def main_dashboard():
#     return render_template('main.html')  # renders main.html

@bp.route("/main")
def main_dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("main.html")


