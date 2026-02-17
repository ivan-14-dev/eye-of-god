#!/usr/bin/env python3
"""
Eye of God - Backend API Server avec WebSocket
"""

import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g, render_template_string
from flask_socketio import SocketIO, emit
import secrets
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

DATABASE = 'devices.db'
TOKEN_EXPIRY_HOURS = 24

# Stockage temps réel
active_sessions = {}  # token -> {user_id, sid}
device_subscriptions = {}  # device_id -> [sids]

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            device_type TEXT,
            imei TEXT,
            last_lat REAL,
            last_lon REAL,
            last_update TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            accuracy REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    ''')
    
    # User test
    test_password = hashlib.sha256('test123'.encode()).hexdigest()
    try:
        cursor.execute(
            'INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)',
            ('test@example.com', test_password, 'Test User')
        )
        user_id = cursor.lastrowid
        cursor.execute(
            'INSERT INTO devices (user_id, name, device_type) VALUES (?, ?, ?)',
            (user_id, 'Mon Smartphone', 'iPhone')
        )
        cursor.execute(
            'INSERT INTO devices (user_id, name, device_type) VALUES (?, ?, ?)',
            (user_id, 'Tablette', 'iPad')
        )
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()

# ============ Auth ============

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_hex(32)

tokens = {}
active_connections = {}

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token requis'}), 401
        
        token = auth_header[7:]
        if token not in tokens:
            return jsonify({'error': 'Token invalide'}), 401
        
        token_data = tokens[token]
        if token_data['expires'] < datetime.now():
            del tokens[token]
            return jsonify({'error': 'Token expiré'}), 401
        
        g.user_id = token_data['user_id']
        g.token = token
        return f(*args, **kwargs)
    return decorated

# ============ Routes ============

@app.route('/')
def index():
    """Page principale avec carte"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '')
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email et mot de passe requis'}), 400
    
    password_hash = hash_password(password)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, email, name FROM users WHERE email = ? AND password_hash = ?',
        (email, password_hash)
    )
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'error': 'Identifiants invalides'}), 401
    
    token = generate_token()
    tokens[token] = {
        'user_id': user['id'],
        'expires': datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    }
    
    return jsonify({
        'token': token,
        'user': {'id': user['id'], 'email': user['email'], 'name': user['name']}
    })

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    token = g.token
    if token in tokens:
        del tokens[token]
    if token in active_connections:
        del active_connections[token]
    return jsonify({'message': 'Déconnexion réussie'})

@app.route('/api/my-devices', methods=['GET'])
@require_auth
def list_devices():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, name, device_type, imei, last_lat, last_lon, last_update FROM devices WHERE user_id = ?',
        (g.user_id,)
    )
    devices = []
    for row in cursor.fetchall():
        devices.append({
            'id': row['id'],
            'name': row['name'],
            'type': row['device_type'],
            'imei': row['imei'],
            'latitude': row['last_lat'],
            'longitude': row['last_lon'],
            'last_update': row['last_update']
        })
    return jsonify({'devices': devices})

@app.route('/api/device/<int:device_id>/location', methods=['GET'])
@require_auth
def get_location(device_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, name, last_lat, last_lon, last_update FROM devices WHERE id = ? AND user_id = ?',
        (device_id, g.user_id)
    )
    device = cursor.fetchone()
    
    if not device:
        return jsonify({'error': 'Appareil non trouvé'}), 404
    
    return jsonify({
        'id': device['id'],
        'name': device['name'],
        'latitude': device['last_lat'] or 48.8566,
        'longitude': device['last_lon'] or 2.3522,
        'timestamp': device['last_update'] or datetime.now().isoformat()
    })

@app.route('/api/device/<int:device_id>/location', methods=['POST'])
@require_auth
def update_location(device_id):
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    accuracy = data.get('accuracy', 0)
    
    if latitude is None or longitude is None:
        return jsonify({'error': 'Latitude et longitude requises'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id FROM devices WHERE id = ? AND user_id = ?',
        (device_id, g.user_id)
    )
    if not cursor.fetchone():
        return jsonify({'error': 'Appareil non trouvé'}), 404
    
    now = datetime.now().isoformat()
    cursor.execute('''
        UPDATE devices SET last_lat = ?, last_lon = ?, last_update = ? WHERE id = ?
    ''', (latitude, longitude, now, device_id))
    
    cursor.execute('''
        INSERT INTO locations (device_id, latitude, longitude, accuracy) VALUES (?, ?, ?, ?)
    ''', (device_id, latitude, longitude, accuracy))
    
    conn.commit()
    
    # Émettre notification temps réel
    location_data = {
        'device_id': device_id,
        'latitude': latitude,
        'longitude': longitude,
        'accuracy': accuracy,
        'timestamp': now
    }
    socketio.emit('location_update', location_data, room=f'device_{device_id}')
    
    return jsonify({'message': 'Localisation mise à jour', 'data': location_data})

@app.route('/api/device/<int:device_id>/history', methods=['GET'])
@require_auth
def get_history(device_id):
    limit = request.args.get('limit', 50, type=int)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id FROM devices WHERE id = ? AND user_id = ?',
        (device_id, g.user_id)
    )
    if not cursor.fetchone():
        return jsonify({'error': 'Appareil non trouvé'}), 404
    
    cursor.execute('''
        SELECT latitude, longitude, accuracy, timestamp FROM locations
        WHERE device_id = ? ORDER BY timestamp DESC LIMIT ?
    ''', (device_id, limit))
    
    history = []
    for row in cursor.fetchall():
        history.append({
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'accuracy': row['accuracy'],
            'timestamp': row['timestamp']
        })
    return jsonify({'history': history})

@app.route('/api/device/add', methods=['POST'])
@require_auth
def add_device():
    data = request.get_json()
    name = data.get('name')
    device_type = data.get('type', 'smartphone')
    imei = data.get('imei')
    
    if not name:
        return jsonify({'error': 'Nom requis'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO devices (user_id, name, device_type, imei) VALUES (?, ?, ?, ?)
    ''', (g.user_id, name, device_type, imei))
    
    device_id = cursor.lastrowid
    conn.commit()
    return jsonify({'id': device_id, 'name': name, 'type': device_type})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

# ============ WebSocket ============

@socketio.on('connect')
def handle_connect():
    print(f'Client connecté: {request.sid}')

@socketio.on('auth')
def handle_auth(data):
    token = data.get('token')
    if token and token in tokens:
        active_connections[token] = {'sid': request.sid, 'user_id': tokens[token]['user_id']}
        emit('authenticated', {'status': 'ok'})
    else:
        emit('error', {'message': 'Auth failed'})

@socketio.on('subscribe')
def handle_subscribe(data):
    device_id = data.get('device_id')
    if device_id:
        socketio.join_room(f'device_{device_id}')
        emit('subscribed', {'device_id': device_id})

# ============ HTML Template ============

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👁️ Eye of God - Tracker</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places"></script>
    <style>
        #map { height: calc(100vh - 120px); border-radius: 10px; }
        .device-card { transition: all 0.3s; cursor: pointer; }
        .device-card:hover { transform: translateY(-3px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .device-card.active { border: 2px solid #0d6efd; }
        .online-indicator { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
        .online { background: #198754; }
        .offline { background: #dc3545; }
        #loading { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 9999; display: flex; justify-content: center; align-items: center; }
    </style>
</head>
<body>
    <div id="loading"><div class="text-white"><i class="fas fa-spinner fa-spin fa-3x"></i><p>Chargement...</p></div></div>
    
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1"><i class="fas fa-eye"></i> Eye of God</span>
            <div>
                <span id="userInfo" class="text-light me-3"></span>
                <button class="btn btn-outline-light btn-sm" onclick="logout()">Déconnexion</button>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-3">
        <div class="row">
            <div class="col-md-3">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <i class="fas fa-mobile-alt"></i> Mes Appareils
                    </div>
                    <div class="card-body" id="deviceList" style="max-height: 400px; overflow-y: auto;">
                        <!-- Devices loaded here -->
                    </div>
                </div>
                <div class="mt-3">
                    <button class="btn btn-success w-100" onclick="addDevice()">
                        <i class="fas fa-plus"></i> Ajouter Appareil
                    </button>
                </div>
            </div>
            <div class="col-md-9">
                <div id="map"></div>
            </div>
        </div>
    </div>

    <!-- Login Modal -->
    <div class="modal fade" id="loginModal" data-bs-backdrop="static">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title"><i class="fas fa-sign-in-alt"></i> Connexion</h5>
                </div>
                <div class="modal-body">
                    <input type="email" id="email" class="form-control mb-2" placeholder="Email" value="test@example.com">
                    <input type="password" id="password" class="form-control mb-2" placeholder="Mot de passe" value="test123">
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary w-100" onclick="login()">Se connecter</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let map, markers = {}, polyline, pathCoords = [];
        let socket, token = localStorage.getItem('token');
        let selectedDevice = null;

        // Initialize
        window.onload = function() {
            if (!token) {
                new bootstrap.Modal(document.getElementById('loginModal')).show();
                document.getElementById('loading').style.display = 'none';
            } else {
                initMap();
                loadDevices();
                initSocket();
            }
        };

        function initMap() {
            map = new google.maps.Map(document.getElementById('map'), {
                center: {lat: 48.8566, lng: 2.3522},
                zoom: 13,
                mapTypeId: 'roadmap'
            });
        }

        async function login() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, password})
            });
            
            if (res.ok) {
                const data = await res.json();
                token = data.token;
                localStorage.setItem('token', token);
                bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
                initMap();
                loadDevices();
                initSocket();
            } else {
                alert('Erreur de connexion');
            }
        }

        async function logout() {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {'Authorization': 'Bearer ' + token}
            });
            localStorage.removeItem('token');
            location.reload();
        }

        async function loadDevices() {
            const res = await fetch('/api/my-devices', {
                headers: {'Authorization': 'Bearer ' + token}
            });
            const data = await res.json();
            
            const list = document.getElementById('deviceList');
            list.innerHTML = data.devices.map(d => `
                <div class="card device-card mb-2 ${selectedDevice === d.id ? 'active' : ''}" onclick="selectDevice(${d.id}, '${d.name}')">
                    <div class="card-body p-2">
                        <i class="fas fa-${d.type === 'iPhone' ? 'apple' : 'tablet-alt'}"></i>
                        <strong>${d.name}</strong><br>
                        <small class="text-muted">${d.latitude ? d.latitude.toFixed(4) + ', ' + d.longitude.toFixed(4) : 'Sans localisation'}</small>
                    </div>
                </div>
            `).join('');
            
            // Update markers
            data.devices.forEach(d => {
                if (d.latitude && d.longitude) {
                    updateMarker(d.id, d.name, d.latitude, d.longitude);
                }
            });
        }

        function selectDevice(id, name) {
            selectedDevice = id;
            loadDevices();
            
            const device = document.querySelector(`[onclick="selectDevice(${id}, '${name}')"]`);
            if (device) device.classList.add('active');
            
            // Subscribe to real-time updates
            if (socket) socket.emit('subscribe', {device_id: id});
        }

        function updateMarker(id, name, lat, lng) {
            if (markers[id]) {
                markers[id].setPosition({lat, lng});
                markers[id].setTitle(name + ' - ' + new Date().toLocaleTimeString());
            } else {
                markers[id] = new google.maps.Marker({
                    position: {lat, lng},
                    map: map,
                    title: name,
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 10,
                        fillColor: '#0d6efd',
                        fillOpacity: 1,
                        strokeColor: '#fff',
                        strokeWeight: 2
                    }
                });
                
                markers[id].addListener('click', () => {
                    map.setCenter({lat, lng});
                    map.setZoom(16);
                });
            }
            map.setCenter({lat, lng});
        }

        function initSocket() {
            socket = io();
            socket.on('connect', () => {
                socket.emit('auth', {token});
            });
            socket.on('authenticated', () => {
                console.log('WebSocket authenticated');
                if (selectedDevice) socket.emit('subscribe', {device_id: selectedDevice});
            });
            socket.on('location_update', (data) => {
                if (selectedDevice === data.device_id) {
                    updateMarker(data.device_id, 'Appareil', data.latitude, data.longitude);
                }
            });
        }

        async function addDevice() {
            const name = prompt('Nom de l\'appareil:');
            if (name) {
                await fetch('/api/device/add', {
                    method: 'POST',
                    headers: {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
                    body: JSON.stringify({name, type: 'smartphone'})
                });
                loadDevices();
            }
        }

        // Simulation de localisation (pour test)
        setInterval(async () => {
            if (selectedDevice && token) {
                const lat = 48.8566 + (Math.random() - 0.5) * 0.01;
                const lng = 2.3522 + (Math.random() - 0.5) * 0.01;
                await fetch(`/api/device/${selectedDevice}/location`, {
                    method: 'POST',
                    headers: {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
                    body: JSON.stringify({latitude: lat, longitude: lng, accuracy: 10})
                });
            }
        }, 5000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🔧 Initialisation de la base de données...")
    init_db()
    print("🚀 Eye of God Server starting...")
    print("   URL: http://localhost:5000")
    print("   Login: test@example.com / test123")
    print("   ⚠️  Remplacez YOUR_API_KEY dans le code par votre clé Google Maps API")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
