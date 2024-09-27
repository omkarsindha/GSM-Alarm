document.addEventListener('DOMContentLoaded', function () {
    fetch('/get-history')
        .then(response => response.json())
        .then(data => {
            const historyTable = document.getElementById('history');
            historyTable.innerHTML = '';
            data.forEach((his) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${his.message}</td>
                `;
                historyTable.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching sensor status:', error));
});
