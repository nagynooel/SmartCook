from flask import render_template

# -- Error handling
# Render error to user
def error(message, code=400):
    return render_template("error.html", e_code = code, message = message), code