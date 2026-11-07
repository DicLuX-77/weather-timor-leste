
import sys
import os
import json

from kafka import KafkaProducer
from dotenv import load_dotenv


# ============================================================
# KONFIGURASAUN
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"))

from collectors.combined_collector import all_data


# ============================================================
# KONFIGURASAUN KAFKA
# ============================================================

KAFKA_SERVER = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:29092"
)

TOPIC = os.getenv(
    "KAFKA_TOPIC",
    "weather_timor"
)


# ============================================================
# KAFKA PRODUCER
# ============================================================

producer = None

try:

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,

        value_serializer=lambda value: json.dumps(
            value,
            ensure_ascii=False
        ).encode("utf-8"),

        request_timeout_ms=30000,
        
    )

    print()
    print("🚀 KAFKA PRODUCER - TEMPU NO KUALIDADE AR")
    print("🇹🇱 TIMOR-LESTE")
    print("=" * 60)

    success = 0

    for data in all_data:

        try:

            future = producer.send(
                TOPIC,
                value=data
            )

            future.get(timeout=30)

            success += 1

            print(
                f"📤 {data['location']:<10} "
                f"→ Kafka ✅ | "
                f"{data['weather']['temperature']}°C | "
                f"AQI {data['air_quality']['aqi']}"
            )

        except Exception as error:

            print(
                f"❌ {data.get('location', 'Unknown')} "
                f"→ Sala: {error}"
            )

    producer.flush()

    print()
    print("=" * 60)

    print(
        f"✅ {success} hosi {len(all_data)} "
        f"dadus haruka ba Kafka ho susesu"
    )

    print(f"📦 Topic: {TOPIC}")

    print("=" * 60)

except Exception as error:

    print()
    print(f"❌ Kafka Producer la konsege hahú: {error}")

    raise SystemExit(1)

finally:

    if producer is not None:
        producer.close()
