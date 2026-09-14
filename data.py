import time
import random
import requests

SERVER_URL = 'http://localhost:5000/api/telemetry'

total_energy_kwh = 0.0  # মোট এনার্জির হিসাব রাখবে

print("Starting 5-Parameter Telemetry Simulator...")

while True:
    try:
        # ১. র্যান্ডম ভোল্টেজ (210V - 235V), কারেন্ট (1.5A - 8.0A), টেম্পারেচার (30°C - 45°C)
        voltage = round(random.uniform(210.0, 235.0), 2)
        current = round(random.uniform(1.5, 8.0), 2)
        temperature = round(random.uniform(30.0, 45.0), 1)

        # ২. পাওয়ার হিসাব: Power (kW) = (Voltage * Current) / 1000
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

        res = requests.post(SERVER_URL, json=payload)
        if res.status_code == 200:
            print(f"[SENT] V: {voltage}V | I: {current}A | Temp: {temperature}°C | P: {power_kw}kW | E: {round(total_energy_kwh, 4)}kWh")

    except Exception as e:
        print(f"Error: Ensure app.py is running! ({e})")

    time.sleep(2)  # প্রতি ২ সেকেন্ড পর পর ডাটা পাঠাবে