import { formatPhoneNumber } from './utils.js';

document.addEventListener('DOMContentLoaded', function () {

    //Setup for webpage
    fetch('/sensor-config')
        .then(response => response.json())
        .then(data => {
            document.getElementById('location').value = data.location;
            document.getElementById('max-temp').value = data.max_temp;
            document.getElementById('hysteresis').value = data.hys;
            document.getElementById('alert-interval').value = data.interval;
            document.getElementById('daily-report').value = data.daily_report_time;
            document.getElementById('armed').checked = data.armed
            document.getElementById('send-daily-report').checked = data.send_daily_report;
            document.getElementById('repeat-alerts').checked = data.repeat_alerts;
            const phoneNumbersTable = document.getElementById('phone-numbers');
            phoneNumbersTable.innerHTML = '';
            data.numbers.forEach((number, index) => {
                let num = formatPhoneNumber(number.number)
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${number.name}</td>
                    <td>${num}</td>
                    <td>${(number.daily_sms == true) ? "Yes" : "No"}</td>
                    <td><a href="/delete-number/${index + 1}" class="delete-button">Delete</a></td>
                `;
                phoneNumbersTable.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching sensor status:', error));

    //Event Listeners for the forms
    document.getElementById('config-form').addEventListener('submit', function (event) {
        event.preventDefault();
        const location = document.getElementById('location').value;
        const max_temp = document.getElementById('max-temp').value;
        const hys = document.getElementById('hysteresis').value;
        const interval = document.getElementById('alert-interval').value;
        const daily_report_time = document.getElementById('daily-report').value;
        const send_daily_report = document.getElementById('send-daily-report').checked;
        const armed = document.getElementById('armed').checked;
        const repeat_alerts = document.getElementById('repeat-alerts').checked;


        fetch('/configure-alarm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                location: location,
                max_temp: max_temp,
                hys: hys,
                interval: interval,
                daily_report_time: daily_report_time,
                send_daily_report: send_daily_report,
                armed: armed,
                repeat_alerts: repeat_alerts
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Configured Alarm Successfully');
                } else {
                    console.error('Error configuring alarm:', data.message);
                }
            })
            .catch(error => console.error('Error configuring alarm:', error));
    });


    document.getElementById('phone-form').addEventListener('submit', function (event) {
        event.preventDefault();

        const name = document.getElementById('name').value;
        const phone = document.getElementById('phone').value;
        const daily_sms = document.getElementById('daily-sms').checked;

        const cleanedPhone = phone.replace(/\D/g, '');

        if (cleanedPhone.length < 10) {
            alert('Phone number must be at least 10 digits long.');
            return;
        }

        fetch('/add-phone-number', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: name, phone: cleanedPhone, daily_sms: daily_sms })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    console.error('Error adding phone number:', data.message);
                }
            })
            .catch(error => console.error('Error adding phone number:', error));
    });
});
