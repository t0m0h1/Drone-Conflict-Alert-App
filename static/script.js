document.getElementById('checkBtn').addEventListener('click', () => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            fetch('/check_aircraft', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lat: lat, lon: lon })
            })
            .then(response => response.json())
            .then(data => {
                const alertsUl = document.getElementById('alerts');
                alertsUl.innerHTML = '';
                if (data.alerts.length === 0) {
                    alertsUl.innerHTML = '<li>No nearby aircraft detected.</li>';
                } else {
                    data.alerts.forEach(alert => {
                        const li = document.createElement('li');
                        li.textContent = `⚠️ Call: ${alert.call}, Distance: ${alert.distance_km} km, Altitude: ${alert.altitude_ft} ft`;
                        alertsUl.appendChild(li);
                    });
                }
            });
        });
    } else {
        alert("Geolocation is not supported by your browser.");
    }
});
