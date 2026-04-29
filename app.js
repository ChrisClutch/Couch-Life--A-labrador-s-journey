const stores = [
  {
    name: "Goodwill Salem South",
    lat: 44.8915,
    lng: -123.0407,
    address: "3535 Commercial St SE, Salem, OR 97302",
    website: "https://meetgoodwill.org/",
    image: "https://maps.googleapis.com/maps/api/streetview?size=800x450&location=3535+Commercial+St+SE+Salem+OR&fov=90"
  },
  {
    name: "St. Vincent de Paul Thrift Store",
    lat: 44.9318,
    lng: -123.0421,
    address: "1860 Broadway St NE, Salem, OR 97301",
    website: "https://www.svdp.us/",
    image: "https://maps.googleapis.com/maps/api/streetview?size=800x450&location=1860+Broadway+St+NE+Salem+OR&fov=90"
  },
  {
    name: "Salvation Army Family Store",
    lat: 44.9324,
    lng: -123.0256,
    address: "2855 Broadway St NE, Salem, OR 97303",
    website: "https://satruck.org/",
    image: "https://maps.googleapis.com/maps/api/streetview?size=800x450&location=2855+Broadway+St+NE+Salem+OR&fov=90"
  },
  {
    name: "Engelberg Antiks & Collectibles",
    lat: 44.9367,
    lng: -123.0354,
    address: "1485 Market St NE, Salem, OR 97301",
    website: "https://engelbergantiques.com/",
    image: "https://maps.googleapis.com/maps/api/streetview?size=800x450&location=1485+Market+St+NE+Salem+OR&fov=90"
  },
  {
    name: "SuperThrift - Union Gospel Mission",
    lat: 44.9491,
    lng: -123.0309,
    address: "626 Lancaster Dr NE, Salem, OR 97301",
    website: "https://ugmsalem.org/superthrift/",
    image: "https://maps.googleapis.com/maps/api/streetview?size=800x450&location=626+Lancaster+Dr+NE+Salem+OR&fov=90"
  }
];

const map = L.map("map").setView([44.9429, -123.0351], 12);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap"
}).addTo(map);

const markers = [];
const storeList = document.getElementById("storeList");
const cardTemplate = document.getElementById("storeCardTemplate");
const statusEl = document.getElementById("status");
let userMarker;

function haversineMiles(a, b) {
  const R = 3958.8;
  const toRad = (x) => x * Math.PI / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const x = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(x));
}

function googleMapsDirections(lat, lng, label) {
  return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&destination_place_id=${encodeURIComponent(label)}`;
}

function streetViewLink(lat, lng) {
  return `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lng}`;
}

function renderStores(origin) {
  storeList.innerHTML = "";
  markers.forEach((m) => map.removeLayer(m));
  markers.length = 0;

  const sorted = [...stores]
    .map((s) => ({ ...s, miles: origin ? haversineMiles(origin, s) : null }))
    .sort((a, b) => (a.miles ?? 999) - (b.miles ?? 999));

  sorted.forEach((store) => {
    const marker = L.marker([store.lat, store.lng]).addTo(map);
    marker.bindPopup(`<strong>${store.name}</strong><br/>${store.address}`);
    markers.push(marker);

    const card = cardTemplate.content.cloneNode(true);
    card.querySelector("h3").textContent = store.name;
    card.querySelector(".address").textContent = store.address;
    card.querySelector(".distance").textContent = store.miles ? `${store.miles.toFixed(1)} miles away` : "Distance: enable location";
    const img = card.querySelector(".store-photo");
    img.src = store.image;
    img.alt = `${store.name} location photo`;
    card.querySelector(".website").href = store.website;
    card.querySelector(".directions").href = googleMapsDirections(store.lat, store.lng, store.name);
    card.querySelector(".streetview").href = streetViewLink(store.lat, store.lng);
    storeList.append(card);
  });
}

renderStores(null);

document.getElementById("locateBtn").addEventListener("click", () => {
  if (!navigator.geolocation) {
    statusEl.textContent = "Geolocation is not supported in this browser.";
    return;
  }

  statusEl.textContent = "Finding your location...";
  navigator.geolocation.getCurrentPosition((position) => {
    const origin = {
      lat: position.coords.latitude,
      lng: position.coords.longitude
    };

    if (userMarker) map.removeLayer(userMarker);
    userMarker = L.marker([origin.lat, origin.lng]).addTo(map).bindPopup("You are here");
    map.setView([origin.lat, origin.lng], 13);
    renderStores(origin);
    statusEl.textContent = "Stores sorted by distance from your location.";
  }, () => {
    statusEl.textContent = "Location access was denied. Showing all stores.";
  });
});
