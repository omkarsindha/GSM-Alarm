document.addEventListener('DOMContentLoaded', function () {

  //Setup for webpage
  fetch('/sensor-config')
    .then(response => response.json())
    .then(data => {
      document.getElementById('lab-temperature').textContent = data.temp + '°C';
      document.getElementById('max-temp').value = data.max_temp;
      document.getElementById('hysteresis').value = data.hys;
      document.getElementById('alert-interval').value = data.interval;
      document.getElementById('daily-report').value = data.daily_report;

      const phoneNumbersTable = document.getElementById('phone-numbers');
      phoneNumbersTable.innerHTML = ''; // Clear existing content
      data.numbers.forEach((number, index) => {
        num = formatPhoneNumber(number.number)
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${number.name}</td>
          <td>${num}</td>
          <td><a href="/delete-number/${index + 1}" class="delete-button">Delete</a></td>
        `;
        phoneNumbersTable.appendChild(row);
      });
    })
    .catch(error => console.error('Error fetching sensor status:', error));

  //Event Listeners for the forms
  document.getElementById('config-form').addEventListener('submit', function (event) {
    event.preventDefault();

    const max_temp = document.getElementById('max-temp').value;
    const hys = document.getElementById('hysteresis').value;
    const interval = document.getElementById('alert-interval').value;
    const daily_report = document.getElementById('daily-report').value;

    fetch('/configure-alarm', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ max_temp: max_temp, hys: hys, interval: interval, daily_report: daily_report })
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          location.reload();
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
      body: JSON.stringify({ name: name, phone: cleanedPhone })
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


function formatPhoneNumber(phoneNumber) {
  const cleanedNumber = phoneNumber.replace(/\D/g, '');

  if (cleanedNumber.length === 11 && cleanedNumber.startsWith('1')) {
    const countryCode = cleanedNumber.slice(0, 1);
    const areaCode = cleanedNumber.slice(1, 4);
    const centralOfficeCode = cleanedNumber.slice(4, 7);
    const lineNumber = cleanedNumber.slice(7, 11);

    return `+${countryCode} (${areaCode}) ${centralOfficeCode}-${lineNumber}`;
  } else {
    throw new Error("Invalid phone number format");
  }
}