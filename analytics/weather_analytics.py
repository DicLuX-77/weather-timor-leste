import os

import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv


# ============================================================
# KONFIGURASAUN
# ============================================================

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://admin:timor123@localhost:27017/?authSource=admin"
)

DATABASE_NAME = "weather_timor"
COLLECTION_NAME = "weather_air_quality"


# ============================================================
# KONEKTA BA MONGODB
# ============================================================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

print()
print("🍃 MongoDB konekta ho susesu! ✅")


# ============================================================
# FOTI DADUS
# ============================================================

dadus = list(
    collection.find(
        {},
        {"_id": 0}
    )
)

print(
    f"📥 Foti {len(dadus)} dadus hosi MongoDB."
)


if not dadus:

    print("❌ La iha dadus atu halo analiza.")
    client.close()
    raise SystemExit


# ============================================================
# KONVERTE BA DATAFRAME
# ============================================================

registos = []

for item in dadus:

    weather = item.get("weather", {})
    air = item.get("air_quality", {})

    registos.append({
        "Fatin": item.get("location"),
        "Latitude": item.get("latitude"),
        "Longitude": item.get("longitude"),
        "Temperatura": weather.get("temperature"),
        "Umidade": weather.get("humidity"),
        "Pressaun": weather.get("pressure"),
        "Anin": weather.get("wind_speed"),
        "Udan": weather.get("rain"),
        "Kondisaun": weather.get("condition"),
        "AQI": air.get("aqi"),
        "PM2.5": air.get("pm2_5"),
        "PM10": air.get("pm10"),
        "CO": air.get("co"),
        "NO": air.get("no"),
        "NO2": air.get("no2"),
        "O3": air.get("o3"),
        "SO2": air.get("so2"),
        "NH3": air.get("nh3"),
        "Timestamp": item.get("timestamp")
    })


df = pd.DataFrame(registos)


# ============================================================
# KONVERTE VALOR NUMERIKU
# ============================================================

koluna_numeriku = [
    "Temperatura",
    "Umidade",
    "Pressaun",
    "Anin",
    "Udan",
    "AQI",
    "PM2.5",
    "PM10",
    "CO",
    "NO",
    "NO2",
    "O3",
    "SO2",
    "NH3"
]

for koluna in koluna_numeriku:

    df[koluna] = pd.to_numeric(
        df[koluna],
        errors="coerce"
    )


# ============================================================
# ANALIZA GERAL
# ============================================================

print()
print("=" * 70)
print("📊 BIG DATA ANALYTICS")
print("🇹🇱 WEATHER & AIR QUALITY TIMOR-LESTE")
print("=" * 70)

print(
    f"💾 Total Dadus : {len(df)}"
)

print(
    f"📍 Total Fatin : {df['Fatin'].nunique()}"
)


# ============================================================
# STATISTIKA GERAL
# ============================================================

print()
print("📈 STATISTIKA GERAL")
print("-" * 70)

koluna_analiza = [
    "Temperatura",
    "Umidade",
    "Pressaun",
    "Anin",
    "AQI",
    "PM2.5",
    "PM10"
]

for koluna in koluna_analiza:

    print(
        f"{koluna:<15} "
        f"Min={df[koluna].min():.2f} | "
        f"Max={df[koluna].max():.2f} | "
        f"Media={df[koluna].mean():.2f}"
    )


# ============================================================
# ANALIZA TUIR FATIN
# ============================================================

print()
print("📍 ANALIZA TUIR FATIN")
print("-" * 70)

analiza_fatin = (
    df.groupby("Fatin")
    .agg(
        Temperatura_Media=("Temperatura", "mean"),
        Umidade_Media=("Umidade", "mean"),
        AQI_Media=("AQI", "mean"),
        PM25_Media=("PM2.5", "mean"),
        Total_Dadus=("Fatin", "count")
    )
    .sort_values(
        "Temperatura_Media",
        ascending=False
    )
)

print(
    analiza_fatin.round(2).to_string()
)


# ============================================================
# SALVA RESULTADU ANALYTICS
# ============================================================

os.makedirs(
    os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "results"
    ),
    exist_ok=True
)

arquivo = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "results",
    "weather_analytics.xlsx"
)

with pd.ExcelWriter(
    arquivo,
    engine="openpyxl"
) as writer:

    df.to_excel(
        writer,
        sheet_name="Dadus",
        index=False
    )

    analiza_fatin.round(2).to_excel(
        writer,
        sheet_name="Analiza Fatin"
    )


print()
print("=" * 70)
print("✅ ANALYTICS REMATA HO SUSSESU!")
print("=" * 70)
print(
    f"📄 Rezultadu: {arquivo}"
)
print("=" * 70)


client.close()