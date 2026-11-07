import os
import json
import requests
from datetime import datetime, timezone

from dotenv import load_dotenv

# Lee file .env
load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Koordenada Dili
LOCATION = "Dili"
LAT = -8.5569
LON = 125.5603

# URL OpenWeather Air Pollution API
URL = "https://api.openweathermap.org/data/2.5/air_pollution"


def get_air_quality(location, latitude, longitude):

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY
    }

    try:

        response = requests.get(
            URL,
            params=params,
            timeout=10
        )

        if response.status_code != 200:

            print(f"❌ Dadus hosi {location} la konsege foti")
            print(response.json())

            return None

        data = response.json()

        # Dadus kualidade ar hosi OpenWeather
        air_data = data["list"][0]

        components = air_data["components"]

        air_quality_data = {

            "location": location,

            "latitude": latitude,

            "longitude": longitude,

            "aqi": air_data["main"]["aqi"],

            "co": components["co"],

            "no": components["no"],

            "no2": components["no2"],

            "o3": components["o3"],

            "so2": components["so2"],

            "pm2_5": components["pm2_5"],

            "pm10": components["pm10"],

            "nh3": components["nh3"],

            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return air_quality_data

    except requests.exceptions.RequestException as error:

        print(f"❌ Sala bainhira foti dadus {location}: {error}")

        return None


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print("\n🌫️ MONITORIZASAUN KUALIDADE AR - DILI")
print("=" * 50)

air_quality = get_air_quality(
    LOCATION,
    LAT,
    LON
)


if air_quality:

    print("\n📦 REZULTADU DADUS JSON")
    print("=" * 50)

    json_data = json.dumps(
        air_quality,
        indent=4,
        ensure_ascii=False
    )

    print(json_data)

    print("\n" + "=" * 50)
    print("✅ Dadus Kualidade Ar Dili konsege foti ho susesu")
    print("=" * 50)