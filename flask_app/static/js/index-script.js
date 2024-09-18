// document.addEventListener("DOMContentLoaded", () => {
//   let temp_form = document.getElementById("temp-form");

//   temp_form.addEventListener("submit", (e) => {
//     e.preventDefault();

//     let max = document.getElementById("max-temp").value;
//     let min = document.getElementById("min-temp").value;

//     fetch("/configure-alarm", {
//       method: "POST",
//       body: JSON.stringify({
//         max_temp: max,
//         min_temp: min
//       }),
//       headers: {
//         "Content-type": "application/json; charset=UTF-8"
//       }
//     })
//       .then((response) => response.json())
//       .then((json) => console.log(json));
//   });
// });


document.addEventListener('DOMContentLoaded', function () {
  fetch('/sensor-config')
    .then(response => response.json())
    .then(data => {
      document.getElementById('lab-temperature').textContent = data.temp + '°C';
      document.getElementById('max-temp').value = data.max_temp;
      document.getElementById('hysteresis').value = data.hys;
      document.getElementById('report-interval').value = data.interval;

      const phoneNumbersTable = document.getElementById('phone-numbers');
      phoneNumbersTable.innerHTML = ''; // Clear existing content
      data.numbers.forEach((number, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${number.name}</td>
          <td>${number.number}</td>
          <td><a href="/delete-number/${index + 1}" class="delete-button">Delete</a></td>
        `;
        phoneNumbersTable.appendChild(row);
      });
    })
    .catch(error => console.error('Error fetching sensor status:', error));


  document.getElementById('config-form').addEventListener('submit', function (event) {
    event.preventDefault(); // Prevent the default form submission

    const max_temp = document.getElementById('max-temp').value;
    const hys = document.getElementById('hysteresis').value;
    const interval = document.getElementById('report-interval').value;

    fetch('/configure-alarm', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ max_temp: max_temp, hys: hys, interval: interval })
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
    event.preventDefault(); // Prevent the default form submission

    const name = document.getElementById('name').value;
    const phone = document.getElementById('phone').value;

    fetch('/add-phone-number', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name: name, phone: phone })
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