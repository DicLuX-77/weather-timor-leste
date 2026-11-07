
import os
import sys
import time
import subprocess

from pymongo import MongoClient
from dotenv import load_dotenv


# ============================================================
# KONFIGURASAUN
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(os.path.join(BASE_DIR, ".env"))

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://admin:password@localhost:27017/?authSource=admin"
)

DATABASE_NAME = "weather_timor"
COLLECTION_NAME = os.getenv(
    "MONGO_COLLECTION",
    "weather_air_quality"
)

INTERVAL = int(os.getenv("INTERVAL", "30"))
META_DADUS = int(os.getenv("META_DADUS", "10000"))

TEMPU_MAX = 120
INTERVAL_CHECK = 5


# ============================================================
# DIRETORIU SCRIPT
# ============================================================

PRODUCER_SCRIPT = os.path.join(
    BASE_DIR,
    "producer",
    "kafka_producer.py"
)

EXCEL_SCRIPT = os.path.join(
    BASE_DIR,
    "storage",
    "update_excel.py"
)


# ============================================================
# KONEKTA BA MONGODB
# ============================================================

client = None

try:

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000
    )

    client.server_info()

    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    print()
    print("🍃 MongoDB konekta ho susesu! ✅")

except Exception as error:

    print()
    print(f"❌ La konsege konekta ba MongoDB: {error}")

    raise SystemExit(1)


# ============================================================
# FUNSAUN FOTI TOTAL DADUS
# ============================================================

def total_dadus():

    return collection.count_documents({})


# ============================================================
# FUNSAUN HALA KAFKA PRODUCER
# ============================================================

def hala_producer():

    print()
    print("=" * 60)
    print("🚀 HAHÚ KAFKA PRODUCER")
    print("=" * 60)

    try:

        result = subprocess.run(
            [sys.executable, PRODUCER_SCRIPT],
            cwd=BASE_DIR,
            check=False
        )

        if result.returncode != 0:

            print("❌ Kafka Producer la konsege haruka dadus.")

            return False

        return True

    except Exception as error:

        print(f"❌ Erro hala Producer: {error}")

        return False


# ============================================================
# FUNSAUN HEIN DADUS IHA MONGODB
# ============================================================

def hein_dadus(total_anterior):

    tempu = 0

    while tempu < TEMPU_MAX:

        total_atual = total_dadus()

        if total_atual > total_anterior:

            return total_atual

        time.sleep(INTERVAL_CHECK)

        tempu += INTERVAL_CHECK

    return total_dadus()


# ============================================================
# FUNSAUN ATUALIZA RELATORIU EXCEL
# ============================================================

def atualiza_excel():

    print()
    print("📊 Atualiza relatoriu Excel...")

    try:

        result = subprocess.run(
            [sys.executable, EXCEL_SCRIPT],
            cwd=BASE_DIR,
            check=False
        )

        if result.returncode == 0:

            print("✅ Relatoriu Excel atualiza ho susesu!")

        else:

            print("⚠️ La konsege atualiza relatoriu Excel.")

    except Exception as error:

        print(f"❌ Erro atualiza Excel: {error}")


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 60)
print("🌦️ WEATHER & AIR QUALITY MONITORING")
print("🇹🇱 TIMOR-LESTE")
print("=" * 60)

print(f"🎯 Meta Dadus : {META_DADUS}")
print(f"⏱️ Intervalu  : {INTERVAL} segundu")
print(f"🍃 Database  : {DATABASE_NAME}")
print(f"📦 Collection: {COLLECTION_NAME}")

print("=" * 60)


# ============================================================
# PROSESU AUTO COLLECTOR
# ============================================================

try:

    while True:

        total_atual = total_dadus()

        print()
        print("=" * 60)

        print(
            f"💾 Total Dadus Agora: {total_atual}/{META_DADUS}"
        )

        print("=" * 60)

        # Haree meta dadus

        if total_atual >= META_DADUS:

            print()
            print("🎉 Meta dadus atinji ona!")

            atualiza_excel()

            break

        # Rai total antes coleta

        total_anterior = total_atual

        # Hala Producer

        producer_ok = hala_producer()

        if not producer_ok:

            print("⚠️ Coleta la susesu. Sei koko fali.")

        else:

            # Hein Consumer rai dadus

            print()
            print("⏳ Hein MongoDB simu dadus hosi Kafka...")

            total_foun = hein_dadus(total_anterior)

            print()
            print(
                f"📥 Total dadus depois coleta: {total_foun}"
            )

            if total_foun > total_anterior:

                print("✅ Dadus foun tama ona iha MongoDB.")

                atualiza_excel()

            else:

                print(
                    "⚠️ Seidauk iha dadus foun iha MongoDB."
                )

        # Haree meta depois coleta

        total_final = total_dadus()

        if total_final >= META_DADUS:

            print()
            print("🎉 Meta dadus 10.000 atinji ona!")

            break

        # Hein antes coleta tuir mai

        print()
        print(f"⏳ Hein {INTERVAL} segundu ba coleta tuir mai...")

        time.sleep(INTERVAL)


except KeyboardInterrupt:

    print()
    print("🛑 Auto Collector para ona.")


except Exception as error:

    print()
    print(f"❌ Auto Collector hetan sala: {error}")

    raise


finally:

    if client is not None:

        client.close()

    print()
    print("✅ Auto Collector taka ona.")
