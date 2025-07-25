from flask import Flask, render_template, request, redirect, url_for, session, flash
from auth.signup import signup_user
from auth.login import login_user

app = Flask(__name__)
app.secret_key = "supersecretkey"

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if signup_user(username, password):
            flash("Signup successful! Please login.", "success")
            return redirect(url_for('login'))
        else:
            flash("Username already exists!", "danger")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if login_user(username, password):
            session['username'] = username
            flash("Login successful!", "success")
            return "Welcome to SecureAuth Dashboard!"  # Later will go to dashboard
        else:
            flash("Invalid credentials or too many attempts!", "danger")
    return render_template('login.html')

if __name__ == "__main__":
    app.run(debug=True)
