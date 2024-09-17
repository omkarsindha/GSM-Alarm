from flask import request, jsonify, render_template
from flask_app import app
from main import get_monitor

main = Blueprint('main', __name__)

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/configure-alarm", methods=["POST"])
def start():
    data = request.get_json()
    max_temp = float(data.get('max_temp'))
    print(f"Max temp: {max_temp}")
    return data

@main.route("/sensor_status", methods=["GET"])
def sensor_status():
    monitor = get_monitor()
    print(monitor)
    if monitor is not None:
        with monitor.lock:
            temp, numbers = monitor.get_config()
            print(numbers)
        return jsonify({"temp": temp, "numbers": numbers})
    else:
        return jsonify({"status": "Monitor not started"}), 500
