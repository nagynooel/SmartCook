from flask import Flask, render_template

from helper import error

app = Flask(__name__)


@app.route('/')
def index():
    return error("Page unavailable!", code=404)


# !! DELETE ON PRODUCTION !!
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)