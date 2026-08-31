import json
import csv
import os
from datetime import datetime
import paho.mqtt.client as mqtt

MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "esp32/airlab/data"
CSV_FILE = "airlab_log.csv"

# Cree le CSV si besoin
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "temp", "hum", "mq135", "pressure_kpa", "dsm_ratio", "pm25", "alert"])

def on_connect(client, userdata, flags, rc):
    print(f"Connecte au broker, code {rc}")
    client.subscribe(MQTT_TOPIC)
    print(f"Abonne a {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        ts = datetime.now().isoformat()

        print(f"[{ts}] {data}")

        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                ts,
                data.get("temp"),
                data.get("hum"),
                data.get("mq135"),
                data.get("pressure_kpa"),
                data.get("dsm_ratio"),
                data.get("pm25"),
                data.get("alert")
            ])

        # Alerte console
        if data.get("alert"):
            print("⚠️  ALERTE - Valeur critique !")

    except Exception as e:
        print(f"Erreur: {e} - payload: {msg.payload}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Connexion a {MQTT_BROKER}...")
client.connect(MQTT_BROKER, 1883, 60)
client.loop_forever()
