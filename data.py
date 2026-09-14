import time
import random
import requests

# ⚠️ সঠিক এন্ডপয়েন্ট: শেষে '/api/telemetry' থাকতে হবে
SERVER_URL = 'https://eprc-server.onrender.com/api/telemetry'

total_energy_kwh = 0.0  # মোট এনার্জির হিসাব রাখবে

print("🚀 Starting 5-Parameter Telemetry Simulator...")
print(f"Connecting to: {SERVER_URL}\n")

while True:
    try:
        # ১. র্যান্ডম ভোল্টেজ (210V - 235V), কারেন্ট (1.5A - 8.0A), টেম্পারেচার (30°C - 45°C)
        voltage = round(random.uniform(210.0, 235.0), 2)
        current = round(random.uniform(1.5, 8.0), 2)
        temperature = round(random.uniform(30.0, 45.0), 1)

        # ২. পাওয়ার হিসাব: Power (kW) = (Voltage * Current) / 1000
        power_kw = round((voltage * current) / 1000.0, 3)

        # ৩. এনার্জি হিসাব: Energy (kWh) = Power (kW) * Hours (২ সেকেন্ড = ২/৩৬০০ ঘণ্টা)
        total_energy_kwh += power_kw * (2 / 3600.0)

        payload = {
            "voltage": voltage,
            "current": current,
            "temperature": temperature,
            "power_kw": power_kw,
            "energy_kwh": round(total_energy_kwh, 4)
        }

        # ১০ সেকেন্ডের টাইমআউট যুক্ত করা হয়েছে যেন সার্ভার রেসপন্স না দিলে আটকে না থাকে
        res = requests.post(SERVER_URL, json=payload, timeout=10)
        
        if res.status_code == 200:
            print(f"✅ [SENT] V: {voltage}V | I: {current}A | Temp: {temperature}°C | P: {power_kw}kW | E: {round(total_energy_kwh, 4)}kWh")
        else:
            print(f"⚠️ [FAILED] Server returned status code: {res.status_code}")

    except requests.exceptions.Timeout:
        print("⏳ [TIMEOUT] Render Server is waking up from sleep mode, retrying...")
    except Exception as e:
        print(f"❌ Error: {e}")

    time.sleep(2)  # প্রতি ২ সেকেন্ড পর পর ডাটা পাঠাবে