import os
import json
import requests
from datetime import datetime, timezone

from dotenv import load_dotenv

# Lee file .env
load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

# ============================================================
# LISTA FATIN TIMOR-LESTE
# 13 MUNISIPIU + ATAURO
# ============================================================

locations = {
    "Dili": (-8.5569, 125.5603),
    "Aileu": (-8.7281, 125.5664),
    "Ainaro": (-9.0118, 125.5080),
    "Atauro": (-8.2425, 125.5756),
    "Baucau": (-8.4667, 126.4500),
    "Bobonaro": (-9.0000, 125.3000),
    "Covalima": (-9.3000, 125.2500),
    "Ermera": (-8.7500, 125.4000),
    "Lautem": (-8.3667, 126.9500),
    "Liquica": (-8.5908, 125.3419),
    "Manatuto": (-8.5167, 126.0167),
    "Manufahi": (-9.0000, 125.9500),
    "Oecusse": (-9.2000, 124.3500),
    "Viqueque": (-8.8500, 126.3667)
}

# URL OpenWeather
URL = "https://api.openweathermap.org/data/2.5/weather"


# ============================================================
# FUNSAUN ATU FOTI DADUS TEMPU
# ============================================================

def get_weather(location, latitude, longitude):

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric",
        "lang": "en"
    }

    try:

        response = requests.get(
            URL,
            params=params,
            timeout=10
        )

        if response.status_code != 200:

            print(f"❌ La konsege foti dadus: {location}")

            return None

        data = response.json()

        # Harii estrutura dadus rasik
        weather_data = {

            "location": location,

            "latitude": latitude,

            "longitude": longitude,

            "temperature": data["main"]["temp"],

            "humidity": data["main"]["humidity"],

            "pressure": data["main"]["pressure"],

            "wind_speed": data["wind"]["speed"],

            "rain": data.get("rain", {}).get("1h", 0),

            "weather": data["weather"][0]["description"],

            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return weather_data

    except requests.exceptions.RequestException as error:

        print(f"❌ Sala bainhira foti dadus {location}: {error}")

        return None


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print("\n🌦️ MONITORIZASAUN TEMPU - TIMOR-LESTE")
print("=" * 50)

all_weather_data = []


for location, coordinates in locations.items():

    latitude, longitude = coordinates

    print(f"📍 Foti dadus: {location}...")

    weather = get_weather(
        location,
        latitude,
        longitude
    )

    if weather:

        all_weather_data.append(weather)

        print(
            f"   ✅ {weather['temperature']}°C | "
            f"Umidade {weather['humidity']}%"
        )


# ============================================================
# OUTPUT JSON
# ============================================================

print("\n")
print("=" * 50)
print("📦 REZULTADU DADUS JSON")
print("=" * 50)

json_data = json.dumps(
    all_weather_data,
    indent=4,
    ensure_ascii=False
)

print(json_data)


# ============================================================
# REZUMU
# ============================================================

print("\n")
print("=" * 50)
print(
    f"✅ Konsege foti dadus hosi "
    f"{len(all_weather_data)} fatin"
)
print("=" * 50)