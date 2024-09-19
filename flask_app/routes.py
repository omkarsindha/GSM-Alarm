from flask import request, jsonify, render_template, redirect, url_for
from flask_app import app
from monitor_instance import get_monitor
from utils.file_utils import add_contact_to_file 
from utils.file_utils import remove_number_by_index
from utils.file_utils import update_config
from utils.utils import format_phone_number


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/configure-alarm", methods=["POST"])
def configure_alarm():
    data = request.get_json()
    max_temp = data.get('max_temp')
    hys = data.get('hys')
    interval = data.get('interval')
    daily_report = data.get('daily_report')
    if max_temp and hys and interval and daily_report:
        update_config(max_temp, hys, interval, daily_report)
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Invalid data"}), 400


@app.route("/sensor-config", methods=["GET"])
def sensor_status():
    monitor = get_monitor()
    if monitor is not None:
        temp, max_temp, hys, interval, daily_report, numbers  = monitor.get_config()
        return jsonify({"temp": temp, "max_temp":max_temp, "hys": hys, "interval":interval, "daily_report": daily_report , "numbers": numbers, })
    else:
        return jsonify({"message": "Monitor not started"}), 500
    
@app.route('/add-phone-number', methods=['POST'])
def add_phone_number():
    data = request.get_json()
    name = data.get('name')
    phone = format_phone_number(data.get('phone'))
    
    if name and phone:
        add_contact_to_file(name, phone)
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Invalid data"}), 400
    
@app.route('/delete-number/<int:index>', methods=['GET'])
def delete_number(index):
    if remove_number_by_index(index):
        return redirect(url_for('home'))
    else:
        return "Index out of range", 404