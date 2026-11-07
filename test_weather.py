import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

if API_KEY:
    print("✅ API key berhasil dibaca dari .env")
else:
    print("❌ API key tidak terbaca")

# Koordinat Dili
LAT = -8.5569
LON = 125.5603

url = "https://api.openweathermap.org/data/2.5/weather"

params = {
    "lat": LAT,
    "lon": LON,
    "appid": API_KEY,
    "units": "metric",
    "lang": "en"
}

response = requests.get(url, params=params)

# Ubah response menjadi JSON terlebih dahulu
data = response.json()

print("Status:", response.status_code)

if response.status_code == 200:

    print("\n=== WEATHER DILI ===")
    print("City        :", data["name"])
    print("Temperature :", data["main"]["temp"], "°C")
    print("Humidity    :", data["main"]["humidity"], "%")
    print("Pressure    :", data["main"]["pressure"], "hPa")
    print("Wind Speed  :", data["wind"]["speed"], "m/s")
    print("Weather     :", data["weather"][0]["description"])

    if "rain" in data:
        print("Rain        :", data["rain"].get("1h", 0), "mm")
    else:
        print("Rain        : 0 mm")

else:

    print("\n❌ API Error")
    print(data)






    <div class="live">
● SISTEMA ONLINE
</div>

</div>