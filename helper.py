from flask import render_template, redirect, flash

from re import match
from werkzeug.security import generate_password_hash, check_password_hash

# -- Global variables
encryption_method = "pbkdf2:sha256:120000"

# -- Error handling
# Render error to user
def error(message, code=400):
    return render_template("error.html", e_code = code, message = message), code


# -- Functions
# - Global
# Redirect user with an alert
def redirect_alert(redirect_to: str, alert_msg:str, alert_type="danger"):
    flash(alert_msg, "alert-" + alert_type)
    return redirect(redirect_to)

# - Registration
# Validate: email address format - returns bool
def validate_email(email: str):
    format = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
    if match(format,email):
        return True
    return False

# Generate hash from password
def generate_hash(password: str):
    werkzeug_hash = generate_password_hash(password, method=encryption_method, salt_length=5).split("$")
    salt = werkzeug_hash[1]
    hash = werkzeug_hash[2]
    return (salt, hash)

# - Login
# Check if the hash matches the password
def check_hash(hash: str, salt: str, password: str):
    return check_password_hash(f"{encryption_method}${salt}${hash}", password)