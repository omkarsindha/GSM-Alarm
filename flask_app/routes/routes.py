from flask import request, jsonify, render_template, redirect, url_for
from flask_socketio import SocketIO
from flask_app import app
from monitor_instance import get_monitor
from utils.file_utils import (
    add_contact_to_file,
    remove_number_by_index,
    update_config,
    get_history_data,
    get_history_data
)
from utils.utils import format_phone_number
import sys

    
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/logs")
def logs():
    return render_template("logs.html")

@app.route("/configure-alarm", methods=["POST"])
def configure_alarm(): 
    data = request.get_json()
    location = data.get('location')
    max_temp = data.get('max_temp')
    hys = data.get('hys')
    interval = data.get('interval')
    daily_report_time = data.get('daily_report_time')
    send_daily_report = data.get('send_daily_report')
    armed = data.get("armed")
    repeat_alerts = data.get("repeat_alerts")
    update_config(location, max_temp, hys, interval, daily_report_time, send_daily_report, armed, repeat_alerts)  
    monitor = get_monitor()
    if monitor is not None:
        monitor.schedule_daily_status()
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Monitor not started/working"}), 400


@app.route("/sensor-config", methods=["GET"])
def sensor_status():
    monitor = get_monitor()
    if monitor is not None:
        config = monitor.get_config()
        return jsonify(config)
    else:
        return jsonify({"success": False, "message": "Monitor not started/working"}), 500
    

@app.route("/get-history", methods=["GET"])
def get_history():
    history = get_history_data()
    if history:
        return jsonify(history)
    else:
        return jsonify({"success": False, "message": "Error"}), 500
    
@app.route('/add-phone-number', methods=['POST'])
def add_phone_number():
    data = request.get_json()
    name = data.get('name')
    phone = format_phone_number(data.get('phone'))
    daily_sms = data.get('daily_sms')
    
    if name and phone:
        add_contact_to_file(name, phone, daily_sms)
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Invalid data"}), 400
    
@app.route('/delete-number/<int:index>', methods=['GET'])
def delete_number(index):
    if remove_number_by_index(index):
        return redirect(url_for('settings'))
    else:
        return jsonify({"success": False, "message": "Index out of range"}), 404
    
