from flask import request, jsonify, render_template, redirect, url_for
from flask_app import app
from monitor_instance import get_monitor
from utils import file_utils
from utils import utils
import sys
import time
    
@app.route("/")
def home():
    monitor = get_monitor()
    config = monitor.get_config()
    return render_template("index.html", **config)

@app.route("/settings")
def settings():
    monitor = get_monitor()
    config = monitor.get_config()
    return render_template("settings.html", **config)

@app.route("/history")
def history():
    history = file_utils.get_history_data()
    return render_template("history.html", history=history)

@app.route("/help")
def help():
    return render_template("help.html")
    
@app.route("/configure-alarm", methods=["POST"])
def configure_alarm(): 
    location = request.form.get('location')
    hys = request.form.get('hys')
    interval = request.form.get('interval')
    daily_report_time = request.form.get('daily_report_time')
    send_daily_report = 'send_daily_report' in request.form
    armed = 'armed' in request.form
    repeat_alerts = 'repeat_alerts' in request.form
    
    file_utils.update_config(location, hys, interval, daily_report_time, send_daily_report, armed, repeat_alerts)  
    monitor = get_monitor()
    monitor.config.load_config()
    monitor.schedule_daily_status()
    return redirect(url_for('settings'))

@app.route('/update_sensor', methods=['POST'])
def update_sensor():
    sensor = request.form['sensor']
    name = request.form['name']
    trigger = request.form['trigger']
    file_utils.update_sensor_data(sensor, name, trigger)
    monitor = get_monitor()
    monitor.config.load_config()
    print(f"Updated {sensor} {name } {trigger}")
    return redirect(url_for('settings'))

@app.route('/add-phone-number', methods=['POST'])
def add_phone_number():
    name = request.form.get('name')
    phone = utils.clean_phone_number(request.form.get('phone'))
    daily_sms = 'daily_sms' in request.form
    admin = 'admin' in request.form
    if name and phone:
        file_utils.add_number_to_file(name, phone, daily_sms, admin)
        monitor = get_monitor()
        monitor.config.load_config()
    return redirect(url_for('settings'))
    
@app.route('/delete-number/<int:index>')
def delete_number(index):
    file_utils.remove_number_by_index(index)
    monitor = get_monitor()
    monitor.config.load_config()
    return redirect(url_for('settings'))

@app.route('/clear_history')
def clear_history():
    file_utils.clear_history()
    return redirect(url_for('history'))

@app.template_filter('format_phone_number')
def format_phone_number(number):
    return f"{number[:2]} ({number[2:5]}) {number[5:8]}-{number[8:]}"

@app.template_filter('change_24h_to_12h')
def change_24h_to_12h(time_24h):
    time_struct = time.strptime(time_24h, "%H:%M")
    time_12hr = time.strftime("%I:%M %p", time_struct)

    return time_12hr

@app.template_filter('round_number')
def round_number(number):
    return round(number)