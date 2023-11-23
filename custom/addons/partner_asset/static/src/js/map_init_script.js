function init_map() {
    var map = L.map('map').setView([parseFloat(latitude), parseFloat(longitude)], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    var marker = L.marker([parseFloat(latitude), parseFloat(longitude)]).addTo(map);
}