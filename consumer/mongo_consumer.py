
import sys
import os
import json
import time

from kafka import KafkaConsumer
from kafka.errors import KafkaError
from dotenv import load_dotenv


# ============================================================
# KONFIGURASAUN
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"))

READY_FILE = "/tmp/consumer-ready"


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

GROUP_ID = "timor-mongodb-storage"


# ============================================================
# STORAGE
# ============================================================

from storage.weather_storage import save_data


# ============================================================
# HAKEREE KONEKSAUN KAFKA
# ============================================================

consumer = None


def prosesa_mensajen(records):

    total = 0

    for partition, messages in records.items():

        for message in messages:

            data = message.value

            if not isinstance(data, dict):

                raise ValueError(
                    "Dadus Kafka la iha formatu JSON object."
                )

            location = data.get(
                "location",
                "Unknown"
            )

            print()
            print(f"📥 Dadus simu: {location}")

            result = save_data(data)

            if not result:

                raise RuntimeError(
                    f"La konsege rai dadus husi {location}."
                )

            print(
                f"✅ {location} rai ona iha MongoDB"
            )

            total += 1

    return total


# ============================================================
# KAFKA CONSUMER
# ============================================================

try:

    # Hamoos sinal kesiade husi execusaun uluk.

    if os.path.exists(READY_FILE):

        os.remove(READY_FILE)


    consumer = KafkaConsumer(

        bootstrap_servers=KAFKA_SERVER,

        group_id=GROUP_ID,

        auto_offset_reset="earliest",

        enable_auto_commit=False,

        value_deserializer=lambda value: json.loads(
            value.decode("utf-8")
        ),

        request_timeout_ms=30000,

        session_timeout_ms=15000,

        heartbeat_interval_ms=5000,

        max_poll_records=100,

        max_poll_interval_ms=300000,

        consumer_timeout_ms=float("inf")

    )

    consumer.subscribe([TOPIC])


    # ========================================================
    # HEADER
    # ========================================================

    print()
    print("=" * 60)
    print("📡 KAFKA → MONGODB STORAGE")
    print("🇹🇱 TIMOR-LESTE")
    print("=" * 60)

    print(f"📦 Topic: {TOPIC}")
    print(f"👥 Group: {GROUP_ID}")
    print("🍃 MongoDB: weather_timor")
    print("⏳ Hein partisaun Kafka...")
    print("=" * 60)


    # ========================================================
    # HAKEREE PARTISAUN NO KESIADE
    # ========================================================

    while not consumer.assignment():

        consumer.poll(timeout_ms=1000)

        if consumer.assignment():

            break

        print(
            "⏳ Consumer seidauk simu partisaun Kafka..."
        )


    # Consumer agora iha partisaun atribuidu.

    with open(READY_FILE, "w", encoding="utf-8") as file:

        file.write("READY")


    print()
    print("=" * 60)
    print("✅ CONSUMER PRONTU!")
    print("⏳ Hein dadus hosi Kafka...")
    print("=" * 60)


    # ========================================================
    # RECEIVE & SAVE DATA
    # ========================================================

    while True:

        records = consumer.poll(
            timeout_ms=1000,
            max_records=100
        )

        if not records:

            continue

        total = prosesa_mensajen(records)

        # Commit deit depois dadus hotu iha batch rai ho susesu.

        consumer.commit()

        print()
        print(
            f"📊 Total dadus rai iha batch ida-ne'e: {total}"
        )

        print(
            "✅ Offset Kafka commit ho susesu."
        )


except KeyboardInterrupt:

    print()
    print("🛑 MongoDB Consumer para ona.")


except Exception as error:

    print()
    print(
        f"❌ Kafka Consumer hetan sala: {error}"
    )

    raise SystemExit(1)


finally:

    if os.path.exists(READY_FILE):

        os.remove(READY_FILE)

    if consumer is not None:

        consumer.close()

        print(
            "✅ Kafka Consumer taka ona."
        )
