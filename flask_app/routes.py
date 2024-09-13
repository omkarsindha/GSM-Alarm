from flask import request, jsonify, render_template
from flask_app import app


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/configure-alarm", methods=["POST"])
def start():
    data = request.get_json()
    max_temp = float(data.get('max_temp'))
    min_temp = float(data.get('min_temp'))
    print(f"{max_temp} ||| {min_temp}")
    return data