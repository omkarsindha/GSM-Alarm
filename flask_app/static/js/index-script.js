import { formatPhoneNumber } from './utils.js';
import { convertTo12Hour } from './utils.js';


document.addEventListener('DOMContentLoaded', function () {
  fetch('/sensor-config')
    .then(response => response.json())
    .then(data => {
      document.getElementById('location').textContent = data.location;

      let armed = document.getElementById('armed')
      armed.textContent = data.armed == true ? "ARMED" : "UN-ARMED";
      armed.style.color = data.armed == true ? "#4CAF50" : "#FF4C4C";

      let temp = document.getElementById('lab-temperature')
      temp.textContent = data.temp + '°C';
      if (data.temp >= data.max_temp) {
        temp.style.color = "#FF4C4C";
      } else if (data.temp > data.max_temp - 4) {
        temp.style.color = "#FFA500";
      } else {
        temp.style.color = "#4CAF50";
      }

      document.getElementById('max-temp').textContent = data.max_temp + '°C';
      document.getElementById('hysteresis').textContent = data.hys + '°C';
      document.getElementById('alert-interval').textContent = data.interval + ' minutes';
      update_signal_strength_icon(data.signal_strength)
      document.getElementById('signal-type').textContent = data.signal_type
      document.getElementById('pi-time').textContent = data.pi_time

      const time = convertTo12Hour(data.daily_report_time)
      document.getElementById('daily-report').textContent = time;

      let send_daily_report = document.getElementById('send-daily-report');
      send_daily_report.textContent = data.send_daily_report == true ? "Yes" : "No";
      send_daily_report.style.color = data.send_daily_report == true ? "#4CAF50" : "#FF4C4C";

      const phoneNumbersTable = document.getElementById('phone-numbers');
      phoneNumbersTable.innerHTML = '';
      data.numbers.forEach((number) => {
        let num = formatPhoneNumber(number.number)
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${number.name}</td>
          <td>${num}</td>
          <td>${(number.daily_sms == true) ? "Yes" : "No"}</td>
        `;
        phoneNumbersTable.appendChild(row);
      });
    })
    .catch(error => console.error('Error fetching sensor status:', error));

});




function update_signal_strength_icon(signal_strength) {
  const signalElement = document.getElementById('signal-strength');
  if (!signalElement) {
    console.error('Element with id "signal-strength" not found.');
    return;
  }
  switch (signal_strength) {
    case 1:
      signalElement.src = "/static/imgs/signal-strength-1.svg";
      break;
    case 2:
      signalElement.src = "/static/imgs/signal-strength-2.svg";
      break;
    case 3:
      signalElement.src = "/static/imgs/signal-strength-3.svg";
      break;
    case 4:
      signalElement.src = "/static/imgs/signal-strength-4.svg";
      break;
    default:
      signalElement.src = "/static/imgs/signal-strength-0.svg";
  }
}
