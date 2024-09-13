document.addEventListener("DOMContentLoaded", () => {
  let temp_form = document.getElementById("temp-form");

  temp_form.addEventListener("submit", (e) => {
    e.preventDefault();

    let max = document.getElementById("max-temp").value;
    let min = document.getElementById("min-temp").value;

    fetch("/configure-alarm", {
      method: "POST",
      body: JSON.stringify({
        max_temp: max,
        min_temp: min
      }),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
    })
    .then((response) => response.json())
    .then((json) => console.log(json));
  });
});