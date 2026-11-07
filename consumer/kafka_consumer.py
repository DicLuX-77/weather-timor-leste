import json
from kafka import KafkaConsumer

# ============================================================
# KONFIGURASAUN KAFKA
# ============================================================

KAFKA_SERVER = "localhost:29092"
TOPIC = "weather_timor"


# ============================================================
# KAFKA CONSUMER
# ============================================================

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_SERVER,
    auto_offset_reset="latest",
    enable_auto_commit=True,
    group_id="timor-weather-monitoring",
    value_deserializer=lambda value: json.loads(
        value.decode("utf-8")
    )
)


# ============================================================
# KABESALHO
# ============================================================

print()
print("📡 KAFKA CONSUMER - TEMPU NO KUALIDADE AR")
print("🇹🇱 TIMOR-LESTE")
print("=" * 60)
print(f"📦 Topic : {TOPIC}")
print("⏳ Hein dadus...")
print("=" * 60)


# ============================================================
# SIMU DADUS
# ============================================================

try:

    for message in consumer:

        data = message.value

        location = data["location"]
        weather = data["weather"]
        air = data["air_quality"]

        print()
        print("📥 DADUS SIMU HOSI KAFKA")
        print("-" * 60)

        print(f"📍 Fatin        : {location}")

        print(
            f"🌡️ Temperatura : "
            f"{weather['temperature']} °C"
        )

        print(
            f"💧 Umidade      : "
            f"{weather['humidity']} %"
        )

        print(
            f"🌬️ Anin         : "
            f"{weather['wind_speed']} m/s"
        )

        print(
            f"🌦️ Kondisaun    : "
            f"{weather['condition']}"
        )

        print(
            f"🌫️ AQI          : "
            f"{air['aqi']}"
        )

        print(
            f"💨 PM2.5        : "
            f"{air['pm2_5']}"
        )

        print(
            f"💨 PM10         : "
            f"{air['pm10']}"
        )

        print(
            f"🕐 Timestamp    : "
            f"{data['timestamp']}"
        )

        print("-" * 60)


except KeyboardInterrupt:

    print()
    print("🛑 Consumer para ona.")


finally:

    consumer.close()
    print("✅ Kafka Consumer taka ona.")