#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// --- CONFIG WIFI / MQTT ---
const char* WIFI_SSID = "TON_WIFI";
const char* WIFI_PASS = "TON_MDP";
const char* MQTT_BROKER = "broker.hivemq.com";
const int   MQTT_PORT = 1883;
const char* MQTT_TOPIC_DATA = "esp32/airlab/data";
const char* MQTT_TOPIC_CMD = "esp32/airlab/cmd";

// --- PINS ---
#define PIN_DHT 4
#define DHT_TYPE DHT22
#define PIN_MQ135 34
#define PIN_DSM501A 16
#define PIN_MPX2010 35
#define PIN_BUZZER 23
#define PIN_RELAY 22

DHT dht(PIN_DHT, DHT_TYPE);
WiFiClient espClient;
PubSubClient mqtt(espClient);

unsigned long lastRead = 0;
const long INTERVAL = 15000; // 15s

// --- DSM501A ---
volatile unsigned long lowPulseOccupancy = 0;
unsigned long startTimeDSM = 0;

void IRAM_ATTR dsmInterrupt() {
  // Mesure durée état LOW (méthode simple)
}

float readMQ135() {
  int raw = analogRead(PIN_MQ135);
  return raw; // à convertir en ppm après calibration
}

float readMPX2010() {
  int raw = analogRead(PIN_MPX2010);
  float voltage = raw * (3.3 / 4095.0);
  // MPX2010DP : 0 à 10kPa -> 0.2V à 4.7V, adapté
  float pressure_kPa = (voltage - 0.2) * (10.0 / 4.5);
  return pressure_kPa;
}

void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i=0; i<length; i++) msg += (char)payload[i];
  msg.trim();
  if (msg == "BUZZER_ON") digitalWrite(PIN_BUZZER, HIGH);
  if (msg == "BUZZER_OFF") digitalWrite(PIN_BUZZER, LOW);
  if (msg == "RELAY_ON") digitalWrite(PIN_RELAY, HIGH);
  if (msg == "RELAY_OFF") digitalWrite(PIN_RELAY, LOW);
}

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void connectMQTT() {
  while (!mqtt.connected()) {
    String clientId = "ESP32-AirLab-" + String(random(0xffff), HEX);
    if (mqtt.connect(clientId.c_str())) {
      mqtt.subscribe(MQTT_TOPIC_CMD);
    } else {
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_MQ135, INPUT);
  pinMode(PIN_MPX2010, INPUT);
  pinMode(PIN_DSM501A, INPUT);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_RELAY, LOW);

  dht.begin();
  connectWiFi();
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(callback);
  startTimeDSM = millis();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  if (!mqtt.connected()) connectMQTT();
  mqtt.loop();

  if (millis() - lastRead > INTERVAL) {
    lastRead = millis();

    float temp = dht.readTemperature();
    float hum = dht.readHumidity();
    float mq135 = readMQ135();
    float pressure = readMPX2010();
    
    // DSM501A - ratio simplifié
    float dsmRatio = 0;
    // Ici: lecture Low Pulse Occupancy sur 15s
    // Exemple: ratio = lowPulseOccupancy / (INTERVAL*10.0)
    float pm25_est = dsmRatio * 100; // estimation à calibrer

    if (isnan(temp) || isnan(hum)) {
      temp = -1; hum = -1;
    }

    // Alarme automatique
    bool alert = false;
    if (mq135 > 2000 || temp > 40) {
      digitalWrite(PIN_BUZZER, HIGH);
      alert = true;
    } else {
      digitalWrite(PIN_BUZZER, LOW);
    }

    // JSON pour MQTT
    char payload[250];
    snprintf(payload, sizeof(payload),
      "{\"temp\":%.1f,\"hum\":%.1f,\"mq135\":%.0f,\"pressure_kpa\":%.2f,\"dsm_ratio\":%.2f,\"pm25\":%.1f,\"alert\":%s}",
      temp, hum, mq135, pressure, dsmRatio, pm25_est, alert ? "true" : "false"
    );

    mqtt.publish(MQTT_TOPIC_DATA, payload);
    Serial.println(payload);
    lowPulseOccupancy = 0;
    startTimeDSM = millis();
  }
}
