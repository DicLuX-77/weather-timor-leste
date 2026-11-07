
import os
import sys
import time
import threading
import subprocess

from datetime import datetime, timezone

from flask import Flask, jsonify, render_template
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv


# ============================================================
# KONFIGURASAUN
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://admin:password@localhost:27017/?authSource=admin"
)

MONGO_DB_NAME = os.getenv(
    "MONGO_DB_NAME",
    "weather_timor"
)

MONGO_COLLECTION_NAME = os.getenv(
    "MONGO_COLLECTION",
    "weather_air_quality"
)

META_DADUS = int(os.getenv("META_DADUS", "10000"))

FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

INTERVALU_ANALYTICS = 15

ENABLE_MANUAL_COLLECTION = (
    os.getenv("ENABLE_MANUAL_COLLECTION", "true").lower()
    in ("true", "1", "yes")
)


# ============================================================
# KONEKTA MONGODB
# ============================================================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000
)

_collection_cache = None
_collection_cache_checked_at = 0.0

_collection_lock = threading.Lock()

_analytics_cache = {
    "time": 0.0,
    "value": None
}

_analytics_lock = threading.Lock()

process_lock = threading.Lock()

process_running = False
process_message = "Sistema prontu."


# ============================================================
# FOTI COLLECTION
# ============================================================

def hetan_collection(force=False):

    global _collection_cache
    global _collection_cache_checked_at

    now = time.time()

    with _collection_lock:

        if _collection_cache is not None and not force:
            return _collection_cache

        if not force and now - _collection_cache_checked_at < 10:
            return _collection_cache

        _collection_cache_checked_at = now

        try:

            client.admin.command("ping")

            db = client[MONGO_DB_NAME]

            collection = db[MONGO_COLLECTION_NAME]

            _collection_cache = collection

            return collection

        except PyMongoError as error:

            app.logger.warning(
                "La konsege asesu MongoDB: %s",
                error
            )

            _collection_cache = None

            return None


# ============================================================
# KONVERTE VALOR NUMERIKU
# ============================================================

def numeric_value(value):

    if isinstance(value, bool) or value is None:
        return None

    try:

        number = float(value)

        if number != number:
            return None

        if number in (float("inf"), float("-inf")):
            return None

        return number

    except (TypeError, ValueError):

        return None


# ============================================================
# FOTI VALOR HOSI KEY
# ============================================================

def first_value(mapping, *keys):

    if not isinstance(mapping, dict):
        return None

    for key in keys:

        if key in mapping and mapping[key] is not None:
            return mapping[key]

    return None


# ============================================================
# NORMALIZA DADUS
# ============================================================

def normaliza_dadus(document):

    weather = document.get("weather") or {}
    air = document.get("air_quality") or {}

    return {

        "location": document.get("location", "-"),

        "latitude": document.get(
            "latitude",
            document.get("lat")
        ),

        "longitude": document.get(
            "longitude",
            document.get("lon")
        ),

        "timestamp": document.get("timestamp", "-"),

        "weather": {

            "temperature": first_value(
                weather,
                "temperature",
                "temp"
            ),

            "humidity": first_value(
                weather,
                "humidity"
            ),

            "pressure": first_value(
                weather,
                "pressure"
            ),

            "wind_speed": first_value(
                weather,
                "wind_speed",
                "wind"
            ),

            "rain": first_value(
                weather,
                "rain",
                "rain_1h",
                "precipitation"
            ),

            "condition": first_value(
                weather,
                "condition",
                "description",
                "main"
            )

        },

        "air_quality": {

            "aqi": first_value(
                air,
                "aqi",
                "AQI"
            ),

            "co": first_value(air, "co", "CO"),
            "no": first_value(air, "no", "NO"),
            "no2": first_value(air, "no2", "NO2"),
            "o3": first_value(air, "o3", "O3"),
            "so2": first_value(air, "so2", "SO2"),

            "pm2_5": first_value(
                air,
                "pm2_5",
                "PM2.5",
                "pm25",
                "PM2_5"
            ),

            "pm10": first_value(
                air,
                "pm10",
                "PM10"
            ),

            "nh3": first_value(
                air,
                "nh3",
                "NH3"
            )

        }

    }


# ============================================================
# STATISTIKA
# ============================================================

def estatistika(lista):

    values = [
        value
        for value in (
            numeric_value(item)
            for item in lista
        )
        if value is not None
    ]

    if not values:

        return {
            "min": 0,
            "max": 0,
            "media": 0,
            "n": 0
        }

    return {

        "min": round(min(values), 2),

        "max": round(max(values), 2),

        "media": round(
            sum(values) / len(values),
            2
        ),

        "n": len(values)

    }


# ============================================================
# ANALYTICS
# ============================================================

def kalkula_analytics(collection):

    now = time.time()

    with _analytics_lock:

        if (
            _analytics_cache["value"] is not None
            and now - _analytics_cache["time"] < INTERVALU_ANALYTICS
        ):

            return _analytics_cache["value"]

        projection = {

            "_id": 0,

            "weather.temperature": 1,
            "weather.temp": 1,
            "weather.humidity": 1,
            "weather.pressure": 1,
            "weather.wind_speed": 1,
            "weather.wind": 1,

            "air_quality": 1

        }

        temperature = []
        humidity = []
        pressure = []
        wind = []
        aqi = []
        pm25 = []
        pm10 = []

        try:

            for doc in collection.find(
                {},
                projection
            ).batch_size(1000):

                weather = doc.get("weather") or {}
                air = doc.get("air_quality") or {}

                pairs = (

                    (
                        temperature,
                        first_value(
                            weather,
                            "temperature",
                            "temp"
                        )
                    ),

                    (
                        humidity,
                        first_value(
                            weather,
                            "humidity"
                        )
                    ),

                    (
                        pressure,
                        first_value(
                            weather,
                            "pressure"
                        )
                    ),

                    (
                        wind,
                        first_value(
                            weather,
                            "wind_speed",
                            "wind"
                        )
                    ),

                    (
                        aqi,
                        first_value(
                            air,
                            "aqi",
                            "AQI"
                        )
                    ),

                    (
                        pm25,
                        first_value(
                            air,
                            "pm2_5",
                            "PM2.5",
                            "pm25",
                            "PM2_5"
                        )
                    ),

                    (
                        pm10,
                        first_value(
                            air,
                            "pm10",
                            "PM10"
                        )
                    )

                )

                for target, value in pairs:

                    number = numeric_value(value)

                    if number is not None:
                        target.append(number)

        except PyMongoError as error:

            app.logger.warning(
                "La konsege kalkula estatistika: %s",
                error
            )

        result = {

            "temperatura": estatistika(temperature),

            "umidade": estatistika(humidity),

            "pressaun": estatistika(pressure),

            "anin": estatistika(wind),

            "aqi": estatistika(aqi),

            "pm25": estatistika(pm25),

            "pm10": estatistika(pm10)

        }

        _analytics_cache.update({

            "time": now,

            "value": result

        })

        return result


# ============================================================
# TIMESTAMP
# ============================================================

def timestamp_sort_key():

    return [("timestamp", -1)]


# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================

@app.get("/")
def dashboard():

    return render_template("index.html")


# ============================================================
# API LIVE
# ============================================================

@app.get("/api/live")
def api_live():

    collection = hetan_collection()

    if collection is None:

        try:

            client.admin.command("ping")

            message = (
                "La hetan collection iha MongoDB."
            )

            status = "empty"

        except PyMongoError:

            message = (
                "MongoDB la konekta. Haree Docker no MONGO_URI."
            )

            status = "offline"

        return jsonify({

            "status": status,

            "mensagem": message,

            "total_dadus": 0,

            "total_fatin": 0,

            "meta": META_DADUS,

            "progresu": 0,

            "estatistika": {},

            "dadus": [],

            "processo": process_running,

            "mensagem_prosesu": process_message,

            "atualiza": datetime.now(
                timezone.utc
            ).isoformat()

        })

    try:

        total = collection.count_documents({})

        locations = collection.distinct("location")

        latest_docs = list(

            collection.find(
                {},
                {"_id": 0}
            )
            .sort(timestamp_sort_key())
            .limit(50)

        )

        latest = [
            normaliza_dadus(doc)
            for doc in latest_docs
        ]

        return jsonify({

            "status": "online",

            "mensagem": "MongoDB konekta.",

            "total_dadus": total,

            "total_fatin": len([
                value
                for value in locations
                if value
            ]),

            "meta": META_DADUS,

            "progresu": round(
                min(total / META_DADUS * 100, 100),
                2
            ),

            "estatistika": kalkula_analytics(collection),

            "dadus": latest,

            "processo": process_running,

            "mensagem_prosesu": process_message,

            "atualiza": datetime.now(
                timezone.utc
            ).isoformat()

        })

    except PyMongoError as error:

        app.logger.exception(
            "Sala lee dadus husi MongoDB"
        )

        return jsonify({

            "status": "offline",

            "mensagem": "Sala lee dadus husi MongoDB.",

            "detallu": str(error)

        }), 503


# ============================================================
# API FOTI DADUS MANUAL
# ============================================================

@app.post("/api/ambil")
def api_ambil():

    global process_running
    global process_message

    # Docker Scheduler mak kontrola coleta automática.

    if not ENABLE_MANUAL_COLLECTION:

        return jsonify({

            "status": "disabled",

            "mensagem": (
                "Coleta manual desativa. "
                "Auto Scheduler mak kontrola prosesu foti dadus."
            )

        }), 403

    if not process_lock.acquire(blocking=False):

        return jsonify({

            "status": "running",

            "mensagem": (
                "Prosesu foti dadus sei lao hela."
            )

        }), 409

    try:

        if process_running:

            return jsonify({

                "status": "running",

                "mensagem": (
                    "Prosesu foti dadus sei lao hela."
                )

            }), 409

        process_running = True

        process_message = (
            "Sistema sei foti dadus hosi OpenWeather API..."
        )

        collection = hetan_collection(force=True)

        if collection is None:

            raise PyMongoError(
                "MongoDB la disponivel."
            )

        before = collection.count_documents({})

        producer_path = os.path.join(
            BASE_DIR,
            "producer",
            "kafka_producer.py"
        )

        if not os.path.isfile(producer_path):

            process_message = (
                "La hetan ficheiru producer/kafka_producer.py."
            )

            return jsonify({

                "status": "error",

                "mensagem": process_message

            }), 404

        env = os.environ.copy()

        env.setdefault(
            "PYTHONIOENCODING",
            "utf-8"
        )

        result = subprocess.run(

            [sys.executable, producer_path],

            cwd=BASE_DIR,

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace",

            timeout=180,

            env=env,

            check=False

        )

        if result.returncode != 0:

            process_message = (
                "Producer la konsege remata. Haree terminal."
            )

            return jsonify({

                "status": "error",

                "mensagem": process_message,

                "saida": (
                    result.stderr or result.stdout or ""
                )[-3000:]

            }), 500

        # Hein dadus foun tama ba MongoDB.

        after = collection.count_documents({})

        max_wait = 120
        elapsed = 0

        while after <= before and elapsed < max_wait:

            time.sleep(2)

            elapsed += 2

            after = collection.count_documents({})

        added = max(after - before, 0)

        _analytics_cache.update({

            "time": 0.0,

            "value": None

        })

        excel_status = "skipped"
        excel_output = ""

        if added > 0:

            process_message = (
                f"Dadus foun {added} tama ona. "
                "Dashboard sei atualiza Excel..."
            )

            excel_path = os.path.join(
                BASE_DIR,
                "storage",
                "update_excel.py"
            )

            if os.path.isfile(excel_path):

                try:

                    excel_result = subprocess.run(

                        [sys.executable, excel_path],

                        cwd=BASE_DIR,

                        capture_output=True,

                        text=True,

                        encoding="utf-8",

                        errors="replace",

                        timeout=120,

                        env=env,

                        check=False

                    )

                    excel_output = (
                        excel_result.stdout or ""
                    )[-3000:]

                    if excel_result.returncode == 0:

                        excel_status = "success"

                        process_message = (
                            f"Prosesu remata. Dadus foun: {added}. "
                            "Excel atualiza ho susesu."
                        )

                    else:

                        excel_status = "error"

                        process_message = (
                            f"Dadus foun {added} tama ona ba MongoDB, "
                            "maibee Excel la konsege atualiza."
                        )

                        excel_output += (
                            "\n" + (excel_result.stderr or "")[-3000:]
                        )

                except subprocess.TimeoutExpired:

                    excel_status = "error"

                    process_message = (
                        "Atualizasaun Excel liu tempu limite."
                    )

            else:

                excel_status = "error"

                process_message = (
                    "La hetan storage/update_excel.py."
                )

        else:

            process_message = (
                "Producer remata, maibee seidauk deteta dadus foun."
            )

        return jsonify({

            "status": "success",

            "dadus_foun": added,

            "total_antes": before,

            "total_depois": after,

            "excel_status": excel_status,

            "mensagem": process_message,

            "saida": (
                result.stdout or ""
            )[-1500:],

            "saida_excel": excel_output

        })

    except subprocess.TimeoutExpired:

        process_message = (
            "Producer liu tempu limite. Haree Kafka no OpenWeather API."
        )

        return jsonify({

            "status": "error",

            "mensagem": process_message

        }), 504

    except PyMongoError as error:

        process_message = (
            "La konsege asesu MongoDB."
        )

        return jsonify({

            "status": "error",

            "mensagem": process_message,

            "detallu": str(error)

        }), 503

    except Exception as error:

        app.logger.exception(
            "Sala iha prosesu foti dadus"
        )

        process_message = (
            "Acontece sala bainhira foti dadus."
        )

        return jsonify({

            "status": "error",

            "mensagem": process_message,

            "detallu": str(error)

        }), 500

    finally:

        process_running = False

        process_lock.release()


# ============================================================
# API HEALTH
# ============================================================

@app.get("/api/health")
def api_health():

    try:

        client.admin.command("ping")

        return jsonify({

            "status": "online",

            "mongodb": "online"

        })

    except PyMongoError:

        return jsonify({

            "status": "offline",

            "mongodb": "offline"

        }), 503


# ============================================================
# HALA DASHBOARD
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("🌦️ WEATHER & AIR QUALITY DASHBOARD")
    print("🇹🇱 TIMOR-LESTE")
    print("=" * 60)

    print(
        f"🌐 Port: {FLASK_PORT}"
    )

    print(
        f"📦 Database: {MONGO_DB_NAME}"
    )

    print(
        f"📁 Collection: {MONGO_COLLECTION_NAME}"
    )

    print(
        f"🎯 Meta dadus: {META_DADUS}"
    )

    print(
        f"🔄 Coleta manual: {ENABLE_MANUAL_COLLECTION}"
    )

    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=FLASK_PORT,
        debug=False,
        threaded=True
    )
