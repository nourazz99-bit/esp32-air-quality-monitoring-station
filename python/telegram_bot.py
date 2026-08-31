import os
import json
import asyncio
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- CONFIG ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC_DATA = "esp32/airlab/data"
MQTT_TOPIC_CMD = "esp32/airlab/cmd"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "MET_TON_TOKEN_ICI")
CHAT_ID_FILE = "chat_id.txt"

last_data = {}

def get_chat_id():
    if os.path.exists(CHAT_ID_FILE):
        with open(CHAT_ID_FILE, "r") as f:
            return f.read().strip()
    return None

def save_chat_id(chat_id):
    with open(CHAT_ID_FILE, "w") as f:
        f.write(str(chat_id))

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print(f"MQTT connecte: {rc}")
    client.subscribe(MQTT_TOPIC_DATA)

def on_message(client, userdata, msg):
    global last_data
    try:
        data = json.loads(msg.payload.decode())
        last_data = data
        print(f"Donnees: {data}")
        # Alerte auto vers Telegram (sera envoye via loop asyncio)
        if data.get("alert"):
            chat_id = get_chat_id()
            if chat_id and userdata.get("app"):
                asyncio.run_coroutine_threadsafe(
                    userdata["app"].bot.send_message(
                        chat_id=chat_id,
                        text=f"🚨 ALERTE AirLab\nTemp: {data['temp']}°C\nMQ135: {data['mq135']}\nPM2.5: {data['pm25']}"
                    ),
                    userdata["loop"]
                )
    except Exception as e:
        print(f"Erreur MQTT: {e}")

# Telegram commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text(
        "✅ Bot AirLab connecte !\n"
        "/status - dernieres valeurs\n"
        "/buzzer_on /buzzer_off\n"
        "/relay_on /relay_off"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not last_data:
        await update.message.reply_text("Aucune donnee recue encore.")
        return
    d = last_data
    await update.message.reply_text(
        f"🌡️ Temp: {d.get('temp')}°C\n"
        f"💧 Hum: {d.get('hum')}%\n"
        f"🏭 MQ135: {d.get('mq135')}\n"
        f"💨 Pression: {d.get('pressure_kpa')} kPa\n"
        f"🌫️ PM2.5: {d.get('pm25')}"
    )

async def send_mqtt_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, cmd: str):
    mqtt_client = context.bot_data["mqtt_client"]
    mqtt_client.publish(MQTT_TOPIC_CMD, cmd)
    await update.message.reply_text(f"Commande envoyee: {cmd}")

async def buzzer_on(update, context): await send_mqtt_cmd(update, context, "BUZZER_ON")
async def buzzer_off(update, context): await send_mqtt_cmd(update, context, "BUZZER_OFF")
async def relay_on(update, context): await send_mqtt_cmd(update, context, "RELAY_ON")
async def relay_off(update, context): await send_mqtt_cmd(update, context, "RELAY_OFF")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # MQTT client
    mqtt_client = mqtt.Client(userdata={"app": app, "loop": loop})
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    mqtt_client.loop_start()

    app.bot_data["mqtt_client"] = mqtt_client

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("buzzer_on", buzzer_on))
    app.add_handler(CommandHandler("buzzer_off", buzzer_off))
    app.add_handler(CommandHandler("relay_on", relay_on))
    app.add_handler(CommandHandler("relay_off", relay_off))

    print("Bot lance...")
    app.run_polling()

if __name__ == "__main__":
    main()
