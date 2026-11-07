import os
import json
import time
import requests

from datetime import datetime, timezone
from dotenv import load_dotenv


# ============================================================
# KARREGA ENVIRONMENT
# ============================================================

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")


# ============================================================
# FATIN TIMOR-LESTE
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


# ============================================================
# API URL
# ============================================================

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

AIR_URL = "https://api.openweathermap.org/data/2.5/air_pollution"


# ============================================================
# GET WEATHER
# ============================================================

def get_weather(latitude, longitude):

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric",
        "lang": "en"
    }

    # Koko dala 3 deit
    for attempt in range(3):

        try:

            response = requests.get(
                WEATHER_URL,
                params=params,
                timeout=20
            )

            if response.status_code != 200:

                print(
                    f"   ⚠️ Sala iha Weather API "
                    f"(Koko {attempt + 1}/3)"
                )

                time.sleep(2)

                continue

            data = response.json()

            return {
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "rain": data.get("rain", {}).get("1h", 0),
                "condition": data["weather"][0]["description"]
            }

        except requests.exceptions.Timeout:

            print(
                f"   ⚠️ Tempu atu simu dadus tempo liu ona. "
                f"Koko fali ({attempt + 1}/3)..."
            )

            time.sleep(2)

        except requests.exceptions.RequestException as error:

            print(
                f"   ❌ Sala iha Weather API: {error}"
            )

            time.sleep(2)

    return None


# ============================================================
# GET AIR QUALITY
# ============================================================

def get_air_quality(latitude, longitude):

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY
    }

    # Koko dala 3 deit
    for attempt in range(3):

        try:

            response = requests.get(
                AIR_URL,
                params=params,
                timeout=20
            )

            if response.status_code != 200:

                print(
                    f"   ⚠️ Sala iha Air Quality API "
                    f"(Koko {attempt + 1}/3)"
                )

                time.sleep(2)

                continue

            data = response.json()

            air = data["list"][0]

            components = air["components"]

            return {
                "aqi": air["main"]["aqi"],
                "co": components["co"],
                "no": components["no"],
                "no2": components["no2"],
                "o3": components["o3"],
                "so2": components["so2"],
                "pm2_5": components["pm2_5"],
                "pm10": components["pm10"],
                "nh3": components["nh3"]
            }

        except requests.exceptions.Timeout:

            print(
                f"   ⚠️ Tempu atu simu dadus kualidade ar liu ona. "
                f"Koko fali ({attempt + 1}/3)..."
            )

            time.sleep(2)

        except requests.exceptions.RequestException as error:

            print(
                f"   ❌ Sala iha Air Quality API: {error}"
            )

            time.sleep(2)

    return None


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print()
print("🌦️🌫️ MONITORIZASAUN TEMPU NO KUALIDADE AR")
print("🇹🇱 TIMOR-LESTE")
print("=" * 60)


all_data = []


for location, coordinates in locations.items():

    latitude, longitude = coordinates

    print(f"📍 Foti dadus: {location}...")

    try:

        # Foti dadus tempu
        weather = get_weather(
            latitude,
            longitude
        )

        # Foti dadus kualidade ar
        air_quality = get_air_quality(
            latitude,
            longitude
        )

        # Karik dadus rua konsege foti
        if weather and air_quality:

            combined_data = {

                "location": location,

                "latitude": latitude,

                "longitude": longitude,

                "weather": weather,

                "air_quality": air_quality,

                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat()
            }

            all_data.append(
                combined_data
            )

            print(
                f"   ✅ "
                f"{weather['temperature']}°C | "
                f"AQI {air_quality['aqi']} | "
                f"PM2.5 {air_quality['pm2_5']}"
            )

        else:

            print(
                "   ❌ Dadus la kompletu"
            )

    except Exception as error:

        print(
            f"   ❌ Sala: {error}"
        )


# ============================================================
# OUTPUT JSON
# ============================================================

print()
print("=" * 60)

print("📦 EVENTU DADUS JSON KOMBINADU")

print("=" * 60)


for data in all_data:

    print(
        json.dumps(
            data,
            ensure_ascii=False
        )
    )


# ============================================================
# REZUMU
# ============================================================

print()
print("=" * 60)

print(
    f"✅ Konsege foti "
    f"{len(all_data)} hosi "
    f"{len(locations)} fatin"
)

print("=" * 60)