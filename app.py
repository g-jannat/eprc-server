import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-secret-key'

# --- ডাটাবেজ কনফিগারেশন ---
DEFAULT_DB = 'postgresql://postgres:123456@localhost:5432/esp32reading'
db_url = os.environ.get('DATABASE_URL', DEFAULT_DB)

# Supabase বা Render-এর URI 'postgres://' দিয়ে শুরু হলে তা 'postgresql://' এ রূপান্তর করে
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ⚠️ Supabase IPv4 Pooler (Port 6543) & SSL Fix
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {
        "sslmode": "require",
        "connect_timeout": 10,
        "options": "-c prepare_threshold=0"
    },
    "pool_pre_ping": True,
    "pool_recycle": 300
}

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- ৫টি প্যারামিটারের ডাটাবেজ মডেল ---
class TelemetryData(db.Model):
    __tablename__ = 'telemetry_data'
    id = db.Column(db.Integer, primary_key=True)
    voltage = db.Column(db.Float, nullable=False)      # V
    current = db.Column(db.Float, nullable=False)      # A
    temperature = db.Column(db.Float, nullable=False)  # °C
    power_kw = db.Column(db.Float, nullable=False)     # kW
    energy_kwh = db.Column(db.Float, nullable=False)   # kWh
    timestamp = db.Column(db.DateTime, default=datetime.now)

# --- ৫টি প্যারামিটার রিসিভ করার এন্ডপয়েন্ট ---
@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400

    voltage = round(float(data.get('voltage', 0.0)), 2)
    current = round(float(data.get('current', 0.0)), 2)
    temperature = round(float(data.get('temperature', 0.0)), 1)
    power_kw = round(float(data.get('power_kw', 0.0)), 3)
    energy_kwh = round(float(data.get('energy_kwh', 0.0)), 4)

    # ১. ডাটাবেজে সেভ
    new_entry = TelemetryData(
        voltage=voltage,
        current=current,
        temperature=temperature,
        power_kw=power_kw,
        energy_kwh=energy_kwh
    )
    db.session.add(new_entry)
    db.session.commit()

    # ২. ফ্রন্টএন্ডে লাইভ ব্রডকাস্ট
    payload = {
        "voltage": voltage,
        "current": current,
        "temperature": temperature,
        "power_kw": power_kw,
        "energy_kwh": energy_kwh,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    socketio.emit('live_telemetry', payload)
    return jsonify({"status": "success"}), 200

@app.route('/')
def index():
    return render_template_string(HTML_DASHBOARD)

# --- ৫টি প্যারামিটার দেখানোর জন্য ড্যাশবোর্ড ---
HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>5-Parameter Telemetry Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5; padding: 30px; text-align: center; }
        .grid-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; margin-top: 20px; }
        .box { background: white; padding: 20px; width: 160px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
        .label { font-size: 13px; color: #666; font-weight: bold; text-transform: uppercase; }
        .value { font-size: 26px; font-weight: bold; color: #007bff; margin-top: 8px; }
        .unit { font-size: 14px; color: #888; }
        .highlight { color: #d97706; }
        .energy { color: #059669; }
    </style>
</head>
<body>
    <h2>⚡ Real-Time Telemetry Dashboard</h2>
    <p>Monitoring 5 Core System Parameters</p>
    
    <div class="grid-container">
        <div class="box"><div class="label">Voltage</div><div class="value"><span id="v">0.0</span> <span class="unit">V</span></div></div>
        <div class="box"><div class="label">Current</div><div class="value"><span id="c">0.0</span> <span class="unit">A</span></div></div>
        <div class="box"><div class="label">Temperature</div><div class="value highlight"><span id="temp">0.0</span> <span class="unit">°C</span></div></div>
        <div class="box"><div class="label">Power</div><div class="value"><span id="p">0.0</span> <span class="unit">kW</span></div></div>
        <div class="box"><div class="label">Energy</div><div class="value energy"><span id="e">0.000</span> <span class="unit">kWh</span></div></div>
    </div>
    
    <p style="margin-top: 25px; color: #555;">Last Updated: <span id="t">--:--:--</span></p>

    <script>
        const socket = io();
        socket.on('live_telemetry', function(data) {
            document.getElementById('v').innerText = data.voltage;
            document.getElementById('c').innerText = data.current;
            document.getElementById('temp').innerText = data.temperature;
            document.getElementById('p').innerText = data.power_kw;
            document.getElementById('e').innerText = data.energy_kwh;
            document.getElementById('t').innerText = data.timestamp;
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)