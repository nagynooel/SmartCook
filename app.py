from flask import Flask, render_template, redirect, flash, request, session
from flask_session import Session

import mysql.connector
from os import environ

from secrets import token_urlsafe

from helper import error, redirect_alert, validate_email, generate_hash, check_hash, create_msg, send_email, check_expiration

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


# Log in to existing account
@app.route("/login", methods=["GET","POST"])
def login():
    # -- POST request
    if request.method == "POST":
        # - Get user input
        username = request.form.get("username")
        password = request.form.get("password")
        
        # - Validate inputs
        # Validate: fields are not empty
        if not username or not password:
            return redirect_alert(f"/login", "Please fill out all fields!")
        
        # Get: hashed password and user id from users table
        c.execute("SELECT hash, salt, id FROM users WHERE UPPER(username) = %s;", (username.upper(),))
        query = c.fetchone()
        
        # Validate: user exists
        if not query:
            return redirect_alert(f"/login", "Incorrect username or password!")
        
        # Split query into variables
        hash, salt, uid = query
        
        # Validate: password matches hash
        if not check_hash(hash, salt, password):
            return redirect_alert(f"/login", "Incorrect username or password!")
        
        # - Log user in
        session["uid"] = uid
        session["username"] = username
        
        return redirect("/")
    
    # -- GET request
    return render_template("login.html")


# Log out from account
@app.route("/logout")
def logout():
    session.clear()
    
    return redirect("/login")


# Send email with reset link
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    # -- POST request
    if request.method == "POST":
        # - Get user input
        email = request.form.get("email").lower()
        
        # - Validate input
        # Validate: field not empty
        if not email:
            return redirect_alert("/reset_password", "Please fill out email field!")
        
        # Validate: email format is valid
        if not validate_email(email):
            return redirect_alert(f"/reset_password", "E-mail address is not valid!")
        
        # Validate: email is registered
        c.execute("SELECT username, id FROM users WHERE email = %s;", (email,))
        query = c.fetchone()
        
        if not query:
            return redirect_alert(f"/reset_password", "Email is not registered!")
        
        username, uid = query
        
        # - Generate reset token and store it in the database
        # Create uniqe token
        unique = False
        token = ""
        
        while not unique:
            token = token_urlsafe(64)
            
            c.execute("SELECT token FROM password_reset_tokens WHERE token = %s;", (token,))
            
            if c.fetchone() is None:
                unique = True
        
        # Insert token into database
        try:
            c.execute("INSERT INTO password_reset_tokens (token, user_id) VALUES (%s, %s);", (token, uid))
            db.commit()
        except Exception as e:
            return error(f"Something went wrong with creating your reset token in our database! Error: {e}", code=500)
        
        c.execute("SELECT expiration_date FROM password_reset_tokens WHERE token = %s;", (token,))
        expiration_date = c.fetchone()[0]
        url = f"{request.url_root}new_password?token={token}"
        
        # - Send password reset email
        try:
            msg = create_msg(email, "Password Reset", render_template("email/reset_password.txt", username=username, url=url, expiration_date=expiration_date), render_template("email/reset_password.html", username=username, url=url, expiration_date=expiration_date))
            
            send_email(msg)
        except Exception() as e:
            return error(f"Something went wrong with sending you the password reset email! Error: {e}", code=500)
        
        return redirect_alert("/reset_password", "Password reset email successfully sent!", "success")
        
    # -- GET request
    return render_template("reset_password.html")


# Create new password
@app.route("/new_password", methods=["GET", "POST"])
def new_password():
    # Validate given token
    # Returns true if valid else returns error message
    def validate_token(token: str):
        # Validate: Token is defined
        if not token:
            return "Token not set!"
        
        # Validate: Token exists
        c.execute("SELECT expiration_date, used FROM password_reset_tokens WHERE token = %s;", (token,))
        query = c.fetchone()
        
        if not query:
            return "Token is invalid!"
        
        # Validate: Token not expired
        expiration, used = query
        
        if check_expiration(expiration):
            return "Token expired! Please request a new one."
        
        # Validate: Token not used
        if used != 0:
            return "Token already used!"
        
        return True
    
    # -- POST request
    if request.method == "POST":
        # - Get user input
        token = request.form.get("token")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        # - Validate inputs
        # Validate: token with nested function 
        token_valid = validate_token(token)
        
        if token_valid != True:
            return redirect_alert("/reset_password", token_valid)
        
        # Validate: fields are not empty
        if not new_password or not confirm_password:
            return redirect_alert(f"/new_password?token={token}", "Please fill out all fields!")
        
        # Validate: passwords match
        if new_password != confirm_password:
            return redirect_alert(f"/new_password?token={token}", "Passwords do not match!")
        
        # - Update user password
        # Get user ID
        c.execute("SELECT user_id FROM password_reset_tokens WHERE token = %s;", (token,))
        query = c.fetchone()
        
        if not query:
            return redirect_alert("/reset_password", "Token is invalid!")
        
        uid = query[0]
        
        # Hash password
        salt, hash = generate_hash(new_password)
        
        # Update password and set token status to used
        try:
            c.execute("UPDATE users SET hash = %s, salt = %s WHERE id = %s;", (hash, salt, uid))
            c.execute("UPDATE password_reset_tokens SET used = True WHERE token = %s;", (token,))
            
            db.commit()
        except Exception() as e:
            return error(f"Something went wrong with changing your password in our database! Error: {e}", code=500)
        
        return redirect_alert("/login", "Password successfully changed!", "success")
    
    # -- GET request
    # - Get token
    token = request.args.get("token")
    
    # Validate: token with nested function 
    token_valid = validate_token(token)
    
    if token_valid != True:
        return redirect_alert("/reset_password", token_valid)
    
    # Token validated user can access new password page
    return render_template("new_password.html", token=token)


# !! DELETE ON PRODUCTION !!
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)