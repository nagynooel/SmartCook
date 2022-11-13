from flask import render_template, redirect, flash

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