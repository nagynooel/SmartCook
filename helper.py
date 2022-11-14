"""
    @package: smartcook
    @author: Noel Nagy
    @website: https://github.com/nagynooel
    ©2022 Noel Nagy - All rights reserved.
"""
# --- Helper file containing functions and flask decorators that are made for use mainly in app.py

from flask import render_template, redirect, flash

from re import match
from werkzeug.security import generate_password_hash, check_password_hash

from os import environ
from email.message import EmailMessage
import smtplib, ssl

from datetime import datetime, timezone

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

# Create email message object
def create_msg(receiver: str, subject: str, plain: str, html: str):
    msg = EmailMessage()
    
    # Generic email headers
    msg["From"] = f'SmartCook <{environ.get("SMTP_EMAIL")}>'
    msg["To"] = receiver
    msg["Subject"] = subject
    
    # Set the plain text body
    msg.set_content(plain)
    
    # Set an alternative HTML body
    msg.add_alternative(html, subtype='html')
    
    return msg

# Send SSL email using credentials and SMTP host set in environ variables
def send_email(msg: EmailMessage):
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(environ.get("SMTP_SERVER"), environ.get("SMTP_PORT"), context=context) as server:
        server.login(environ.get("SMTP_EMAIL"), environ.get("SMTP_PASSWORD"))
        server.sendmail(
            environ.get("SMTP_EMAIL"), msg["To"], msg.as_string()
        )

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

# - Password reset
# Check if given expiration date "expired" or not - returns True if expired otherwise False
def check_expiration(expiration, exp_timezone=timezone.utc):
    expiration_date = expiration.replace(tzinfo=exp_timezone)
    current_datetime = datetime.now(exp_timezone)
    
    # Throw error if token already expired
    if current_datetime > expiration_date:
        return True
    
    return False