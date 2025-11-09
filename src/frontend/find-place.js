const placesData = {
    'cafeteria': {
        name: 'Cafeteria',
        building: 'Building B',
        floors: { 'G': 'Ground Floor', '1': 'Mezzanine Level' },
        landmarks: [
            'Start at main entrance',
            'Pass by fountain (left side)',
            'Walk past reception desk',
            'Enter Building B through glass doors',
            'Follow blue directional signs',
            'Arrive at cafeteria'
        ],
        directionsG: 'Exit main entrance, turn left past fountain, walk 50m, enter Building B, cafeteria is ahead',
        directions1: 'Exit main entrance, go right, use elevator to mezzanine level, cafeteria is near stairs',
        distance: '100m',
        time: '2 min walk'
    },
    'library': {
        name: 'Library',
        building: 'Building C',
        floors: { '2': '2nd Floor', '3': '3rd Floor' },
        landmarks: [
            'Start at main atrium',
            'Head towards Building C (east wing)',
            'Pass by information counter',
            'Take large central staircase',
            'Reach 2nd floor landing',
            'Look for library entrance sign',
            'Arrive at main library'
        ],
        directions2: 'Exit main entrance, turn right, enter Building C, take central stairs to 2nd floor',
        directions3: 'Exit main entrance, turn right, enter Building C, use elevator to 3rd floor for archives',
        distance: '150m',
        time: '3 min walk'
    },
    'lab': {
        name: 'Science Lab',
        building: 'Building A',
        floors: { '1': '1st Floor', '2': '2nd Floor' },
        landmarks: [
            'Start at main entrance hall',
            'Look for chemistry signage',
            'Pass biology department',
            'Go up stairs to 1st floor',
            'Pass through equipment storage',
            'Reach lab entrance'
        ],
        directions1: 'From entrance, turn right, go up stairs, first door on left',
        directions2: 'From entrance, turn right, use elevator to 2nd floor, lab is on south wing',
        distance: '80m',
        time: '2 min walk'
    },
    'washroom': {
        name: 'Washroom',
        building: 'Building A',
        floors: { 'G': 'Ground Floor', '1': '1st Floor' },
        landmarks: [
            'From current location',
            'Look for restroom sign (blue)',
            'Head right from corridor',
            'Pass the water cooler',
            'Reach washroom'
        ],
        directionsG: 'Turn right, walk 20m, follow blue signs',
        directions1: 'From corridor, turn left, second door on left',
        distance: '20m',
        time: '30 sec walk'
    },
    'auditorium': {
        name: 'Main Auditorium',
        building: 'Building D',
        floors: { 'G': 'Ground Floor' },
        landmarks: [
            'Exit through main entrance',
            'Head straight across quad',
            'Pass under covered walkway',
            'Large entrance doors visible',
            'Enter main auditorium'
        ],
        directionsG: 'Exit main entrance, walk straight across quad for 200m, large building on right',
        distance: '250m',
        time: '5 min walk'
    },
    'admin office': {
        name: 'Admin Office',
        building: 'Building A',
        floors: { '1': '1st Floor' },
        landmarks: [
            'From entrance hall',
            'Locate main elevator bank',
            'Go to 1st floor',
            'Exit elevator, turn left',
            'Pass marble corridor',
            'Door with gold nameplate'
        ],
        directions1: 'Take elevator to 1st floor, turn left, second door on right',
        distance: '50m',
        time: '1 min walk'
    }
};

function searchPlace(event) {
    event.preventDefault();

    const searchInput = document.getElementById('place-search');
    const floorSelect = document.getElementById('floor-select');
    const query = searchInput.value.trim().toLowerCase();
    const selectedFloor = floorSelect.value;
    const resultsDiv = document.getElementById('search-results');

    if (!query) {
        resultsDiv.innerHTML = '<p class="no-results">Please enter a place name</p>';
        return;
    }

    const matches = Object.keys(placesData).filter(key =>
        key.includes(query) || placesData[key].name.toLowerCase().includes(query)
    );

    if (matches.length === 0) {
        resultsDiv.innerHTML = '<p class="no-results">No places found. Try: cafeteria, library, lab, washroom, auditorium, admin office</p>';
        return;
    }

    const place = placesData[matches[0]];

    let directionText = '';
    if (selectedFloor) {
        const dirKey = 'directions' + selectedFloor;
        directionText = place[dirKey] || 'Directions not available for this floor';
    } else {
        directionText = Object.values(place).find(val => typeof val === 'string' && val.includes('turn'));
    }

    const landmarksList = place.landmarks
        .map((landmark, idx) => `<li><span class="landmark-number">${idx + 1}</span> ${landmark}</li>`)
        .join('');

    resultsDiv.innerHTML = `
        <div class="place-result">
            <h3>${place.name}</h3>
            <div class="place-info">
                <div class="info-row">
                    <span class="info-label">Building:</span>
                    <span>${place.building}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Distance:</span>
                    <span>${place.distance}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Walking Time:</span>
                    <span>${place.time}</span>
                </div>
            </div>

            <div class="visual-path">
                <div class="path-icon">🛣️</div>
                <p>Floor Plan Map Would Display Here</p>
            </div>

            <div class="directions-box">
                <h4>Quick Directions:</h4>
                <p>${directionText}</p>
            </div>

            <div class="landmarks-section">
                <h4>Follow These Landmarks:</h4>
                <ol class="landmarks-list">
                    ${landmarksList}
                </ol>
            </div>
        </div>
    `;
}
