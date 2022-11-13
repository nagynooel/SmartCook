from flask import Flask, render_template, redirect, flash, request, session
from flask_session import Session

import mysql.connector
from os import environ

from helper import error, redirect_alert, validate_email, generate_hash

# -- Configure application
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = environ.get("APP_SECRET_KEY")

# - Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# - Database connection
db = mysql.connector.connect(
    host = environ.get("DATABASE_HOST"),
    user = environ.get("DATABASE_USER"),
    password = environ.get("DATABASE_PASSWORD"),
    database = environ.get("DATABASE_NAME")
)

c = db.cursor(buffered=True)


# -- Routes
@app.route('/')
def index():
    return error("Page unavailable!", code=404)


# - Login and new user functionality
# Register new user
@app.route("/register", methods=["GET","POST"])
def register():
    # -- POST request
    if request.method == "POST":
        # - Get user input
        username = request.form.get("username")
        email = request.form.get("email").lower()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm-password")
        
        # - Validate inputs
        
        # Validate: all fields are filled out
        if not username or not email or not password or not confirm_password:
            return redirect_alert(f"/register?username={username}&email={email}", "Please fill out all fields!")
        
        # Validate: terms accepted
        if not request.form.get("terms-check"):
            return redirect_alert(f"/register?username={username}&email={email}", "Please read and accept terms and conditions to proceed!")
        
        # Validate: email format is valid
        if not validate_email(email):
            return redirect_alert(f"/register?username={username}", "E-mail address is not valid!")
        
        # Confirm: username is not already in database
        c.execute("SELECT username FROM users WHERE UPPER(username) = %s;", (username.upper(),))
        query = c.fetchone()
        
        if query is not None:
            return redirect_alert(f"/register?email={email}", "Username already exists!")
        
        # Confirm: email is not already in database
        c.execute("SELECT email FROM users WHERE email = %s;", (email,))
        query = c.fetchone()
        
        if query is not None:
            return redirect_alert(f"/register?username={username}", "E-mail address is already registered!")
        
        # Validate: password and confirm_password fields match
        if password != confirm_password:
            return redirect_alert(f"/register?username={username}&email={email}", "Passwords do not match!")
        
        # - Register user
        salt, hash = generate_hash(password)
        
        try:
            c.execute("INSERT INTO users (username, email, hash, salt) VALUES (%s, %s, %s, %s);", (username, email, hash, salt))
            c.execute("SELECT LAST_INSERT_ID();")
            db.commit()
        except Exception as e:
            return error(f"Something went wrong with registering you to our database! Error: {e}", code=500)
        
        # Log user in
        uid = c.fetchone()[0]
        
        session["uid"] = uid
        session["username"] = username
        
        return redirect_alert("/", "Registration is successful!", "success")
    
    # -- GET request
    # Autofill data from url
    username = request.args.get("username").strip() if request.args.get("username") else ""
    email = request.args.get("email").strip() if request.args.get("email") else ""
    
    return render_template("register.html", username=username, email=email)


# !! DELETE ON PRODUCTION !!
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)