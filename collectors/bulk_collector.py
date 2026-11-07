
import os
import sys
import time
import subprocess
import requests

from datetime import datetime, timezone
from dotenv import load_dotenv
from kafka import KafkaProducer
from pymongo import MongoClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("OPENWEATHER_API_KEY")

KAFKA_SERVER = "localhost:29092"
TOPIC = "weather_timor"

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://admin:timor123@localhost:27017/?authSource=admin"
)

TARGET_RECORDS = 10000
INTERVAL_SECONDS = 15
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
BATCH_SIZE = 14

LOCATIONS = [
    {"name": "Dili", "lat": -8.5569, "lon": 125.5603},
    {"name": "Aileu", "lat": -8.7281, "lon": 125.5664},
    {"name": "Ainaro", "lat": -9.0118, "lon": 125.5080},
    {"name": "Atauro", "lat": -8.2425, "lon": 125.5756},
    {"name": "Baucau", "lat": -8.4667, "lon": 126.4500},
    {"name": "Bobonaro", "lat": -9.0000, "lon": 125.3000},
    {"name": "Covalima", "lat": -9.3000, "lon": 125.2500},
    {"name": "Ermera", "lat": -8.7500, "lon": 125.4000},
    {"name": "Lautem", "lat": -8.3667, "lon": 126.9500},
    {"name": "Liquica", "lat": -8.5908, "lon": 125.3419},
    {"name": "Manatuto", "lat": -8.5167, "lon": 126.0167},
    {"name": "Manufahi", "lat": -9.0000, "lon": 125.9500},
    {"name": "Oecusse", "lat": -9.2000, "lon": 124.3500},
    {"name": "Viqueque", "lat": -8.8500, "lon": 126.3667},
]


def hatudu(mensagem):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {mensagem}")


def foti_total_mongo():
    cliente = None

    try:
        cliente = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        cliente.admin.command("ping")
        base_dadus = cliente["weather_timor"]

        for naran_koleksaun in base_dadus.list_collection_names():
            koleksaun = base_dadus[naran_koleksaun]

            ezemplu = koleksaun.find_one({
                "weather": {"$exists": True},
                "air_quality": {"$exists": True}
            })

            if ezemplu:
                total = koleksaun.count_documents({})
                hatudu(f"Total dadus iha MongoDB: {total}")
                return total

        hatudu(
            "⚠️ Koleksaun dadus weather no air_quality seidauk hetan."
        )
        return 0

    except Exception as erro:
        hatudu(f"❌ Erro MongoDB: {erro}")
        raise

    finally:
        if cliente:
            cliente.close()


def foti_api(url, parametros):
    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            resposta = requests.get(
                url,
                params=parametros,
                timeout=REQUEST_TIMEOUT
            )

            resposta.raise_for_status()
            return resposta.json()

        except requests.RequestException as erro:
            hatudu(
                f"⚠️ API tentativa {tentativa}/{MAX_RETRIES}: {erro}"
            )

            if tentativa < MAX_RETRIES:
                time.sleep(3)

    return None


def foti_dadus_fatin(fatin):
    parametros = {
        "lat": fatin["lat"],
        "lon": fatin["lon"],
        "appid": API_KEY,
        "units": "metric",
        "lang": "en"
    }

    dadus_weather = foti_api(
        "https://api.openweathermap.org/data/2.5/weather",
        parametros
    )

    dadus_air = foti_api(
        "https://api.openweathermap.org/data/2.5/air_pollution",
        parametros
    )

    if not dadus_weather or not dadus_air:
        hatudu(f"❌ API la konsege foti dadus ba {fatin['name']}.")
        return None

    weather = {
        "temperature": dadus_weather.get("main", {}).get("temp"),
        "humidity": dadus_weather.get("main", {}).get("humidity"),
        "pressure": dadus_weather.get("main", {}).get("pressure"),
        "wind_speed": dadus_weather.get("wind", {}).get("speed", 0),
        "rain": dadus_weather.get("rain", {}).get("1h", 0),
        "condition": (
            dadus_weather.get("weather", [{}])[0].get("description", "N/A")
        )
    }

    air_data = dadus_air.get("list", [{}])[0]
    air_components = air_data.get("components", {})

    air_quality = {
        "AQI": air_data.get("main", {}).get("aqi"),
        "CO": air_components.get("co"),
        "NO": air_components.get("no"),
        "NO2": air_components.get("no2"),
        "O3": air_components.get("o3"),
        "SO2": air_components.get("so2"),
        "PM2.5": air_components.get("pm2_5"),
        "PM10": air_components.get("pm10"),
        "NH3": air_components.get("nh3")
    }

    dadus = {
        "location": fatin["name"],
        "latitude": fatin["lat"],
        "longitude": fatin["lon"],
        "weather": weather,
        "air_quality": air_quality,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    return dadus


def kria_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,
        value_serializer=lambda dadus: __import__("json").dumps(
            dadus,
            ensure_ascii=False
        ).encode("utf-8"),
        acks="all",
        retries=5,
        request_timeout_ms=30000,
        max_block_ms=30000
    )


def atualiza_excel():
    script_excel = os.path.join(
        BASE_DIR,
        "storage",
        "update_excel.py"
    )

    if not os.path.isfile(script_excel):
        hatudu(
            "⚠️ Arquivu storage/update_excel.py la hetan. "
            "Excel seidauk atualiza."
        )
        return False

    ambiente = os.environ.copy()
    ambiente["PYTHONIOENCODING"] = "utf-8"

    try:
        resultado = subprocess.run(
            [sys.executable, script_excel],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=ambiente,
            timeout=180
        )

        if resultado.returncode == 0:
            hatudu("📊 Relatóriu Excel atualiza ho susesu!")

            if resultado.stdout.strip():
                print(resultado.stdout.strip())

            return True

        hatudu("⚠️ Excel la konsege atualiza.")

        if resultado.stderr.strip():
            print(resultado.stderr.strip())

        if resultado.stdout.strip():
            print(resultado.stdout.strip())

        return False

    except subprocess.TimeoutExpired:
        hatudu("⚠️ Atualizasaun Excel liu tempu limite.")
        return False

    except Exception as erro:
        hatudu(f"⚠️ Erro bainhira atualiza Excel: {erro}")
        return False


def main():
    if not API_KEY:
        hatudu("❌ OPENWEATHER_API_KEY la hetan iha ficheiru .env.")
        return

    try:
        total_atual = foti_total_mongo()
    except Exception:
        hatudu("❌ Labele lee total dadus husi MongoDB.")
        return

    if total_atual >= TARGET_RECORDS:
        hatudu(
            f"✅ Meta atinji ona: {total_atual}/{TARGET_RECORDS} dadus."
        )
        return

    faltante = TARGET_RECORDS - total_atual

    hatudu("🌦️ Hahú prosesu rekolla dadus Weather no Air Quality.")
    hatudu(f"🎯 Meta: {TARGET_RECORDS} dadus.")
    hatudu(f"📥 Falta atu kompleta: {faltante} dadus.")
    hatudu(f"📍 Total fatin: {len(LOCATIONS)}.")

    producer = None
    total_enviadu = 0
    batch_enviadu = 0

    try:
        producer = kria_producer()

        while total_enviadu < faltante:
            hatudu("🔄 Hahú rekolla dadus foun...")

            for fatin in LOCATIONS:
                if total_enviadu >= faltante:
                    break

                dadus = foti_dadus_fatin(fatin)

                if dadus is None:
                    continue

                try:
                    producer.send(TOPIC, value=dadus).get(timeout=30)

                    total_enviadu += 1
                    batch_enviadu += 1

                    hatudu(
                        f"✅ Dadus {total_enviadu}/{faltante} "
                        f"| Fatin: {fatin['name']}"
                    )

                except Exception as erro:
                    hatudu(
                        f"❌ Falha haruka dadus ba Kafka "
                        f"({fatin['name']}): {erro}"
                    )

            producer.flush()

            if batch_enviadu > 0:
                hatudu(
                    f"📦 Batch remata. Dadus haruka iha prosesu ida-ne'e: "
                    f"{total_enviadu}."
                )

                hatudu(
                    "⏳ Hein segundu 5 atu fó tempu ba consumer "
                    "atu rai dadus iha MongoDB..."
                )
                time.sleep(5)

                atualiza_excel()
                batch_enviadu = 0

            if total_enviadu < faltante:
                hatudu(
                    f"⏳ Atu kontinua rekolla, hein "
                    f"{INTERVAL_SECONDS} segundu..."
                )
                time.sleep(INTERVAL_SECONDS)

        producer.flush()

        hatudu("🏁 Prosesu haruka dadus remata.")

    except KeyboardInterrupt:
        hatudu("⏹️ Prosesu para hosi utilizadór.")

    except Exception as erro:
        hatudu(f"❌ Erro durante prosesu: {erro}")

    finally:
        if producer is not None:
            producer.flush()
            producer.close()

    try:
        total_final = foti_total_mongo()
        hatudu(
            f"📊 Total ikus iha MongoDB: "
            f"{total_final}/{TARGET_RECORDS}."
        )
        hatudu(
            f"📈 Dadus ne'ebé prosesu ida-ne'e haruka: {total_enviadu}."
        )

    except Exception:
        hatudu(
            "⚠️ Labele konfirma total ikus iha MongoDB. "
            "Favor verifika dashboard ka MongoDB."
        )

    atualiza_excel()


if __name__ == "__main__":
    main()