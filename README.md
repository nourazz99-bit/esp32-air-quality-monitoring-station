# esp32-air-quality-monitoring-station
Station IoT de surveillance qualité de l'air - ESP32 + DHT22 + MQ135 + MPX2010DP + DSM501A + RTC + TFT + Telegram + Ventilation auto - PFE Ingénieur Instrumentation
# AirLab ESP32 - Station Qualité Air

Projet ESP32 avec capteurs : DHT22 (temp/hum), MQ135 (qualité air), DSM501A (poussières), MPX2010DP (pression), Buzzer, Relais.

## 📁 Structure
```
firmware/src/main.cpp      -> Code ESP32
firmware/platformio.ini     -> Config PlatformIO
python/telegram_bot.py      -> Bot Telegram + MQTT
python/mqtt_subscriber.py   -> Logger CSV local
python/requirements.txt     -> Dépendances Python
```

## 🚀 Installation rapide

### 1. Firmware ESP32
1. Installe [VS Code + PlatformIO](https://platformio.org/)
2. Ouvre le dossier `firmware`
3. Modifie WIFI_SSID / WIFI_PASS dans `main.cpp`
4. Branche ton ESP32 et clique sur Upload

Câblage :
- DHT22 -> GPIO4
- MQ135 -> GPIO34 (ADC)
- DSM501A -> GPIO16
- MPX2010DP -> GPIO35 (ADC)
- Buzzer -> GPIO23
- Relais -> GPIO22

### 2. Python
```bash
cd python
pip install -r requirements.txt

# Logger simple
python mqtt_subscriber.py

# Bot Telegram (mettre ton token)
export TELEGRAM_TOKEN="ton_token"
python telegram_bot.py
```

### 3. MQTT
Broker public : `broker.hivemq.com`
- Topic data : `esp32/airlab/data`
- Topic commandes : `esp32/airlab/cmd`
  - `BUZZER_ON / BUZZER_OFF`
  - `RELAY_ON / RELAY_OFF`

## 📊 Format JSON envoye
```json
{"temp":24.5,"hum":55.2,"mq135":1250,"pressure_kpa":2.35,"dsm_ratio":0.12,"pm25":12.5,"alert":false}
```

## Licence
MIT
