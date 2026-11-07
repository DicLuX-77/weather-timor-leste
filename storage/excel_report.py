import os
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
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

ARQUIVU_EXCEL = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "weather_timor_report.xlsx"
)


# ============================================================
# KONEKTA BA MONGODB
# ============================================================

try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )

    client.server_info()

    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    print()
    print("🍃 MongoDB konekta ho susesu! ✅")

except Exception as error:
    print(f"❌ La konsege konekta ba MongoDB: {error}")
    raise SystemExit


# ============================================================
# FOTI DADUS HOSI MONGODB
# ============================================================

dadus = list(
    collection.find(
        {},
        {"_id": 0}
    ).sort("timestamp", 1)
)

print(f"📥 Dadus ne'ebé hetan: {len(dadus)}")


if len(dadus) == 0:
    print("⚠️ Seidauk iha dadus iha MongoDB.")
    raise SystemExit


# ============================================================
# KRIA EXCEL
# ============================================================

workbook = Workbook()

folha_dadus = workbook.active
folha_dadus.title = "Dadus"

folha_resumu = workbook.create_sheet("Resumu")

folha_statistik = workbook.create_sheet("Statistik")


# ============================================================
# FOLHA 1 — DADUS
# ============================================================

koluna = [
    "Fatin",
    "Latitude",
    "Longitude",
    "Temperatura (°C)",
    "Umidade (%)",
    "Pressaun (hPa)",
    "Anin (m/s)",
    "Udan (mm)",
    "Kondisaun",
    "AQI",
    "CO",
    "NO",
    "NO2",
    "O3",
    "SO2",
    "PM2.5",
    "PM10",
    "NH3",
    "Timestamp"
]

folha_dadus.append(koluna)

for cell in folha_dadus[1]:
    cell.font = Font(bold=True)
    cell.alignment = Alignment(horizontal="center")


for data in dadus:

    weather = data.get("weather", {})
    air = data.get("air_quality", {})

    linha = [
        data.get("location"),
        data.get("latitude"),
        data.get("longitude"),

        weather.get("temperature"),
        weather.get("humidity"),
        weather.get("pressure"),
        weather.get("wind_speed"),
        weather.get("rain"),
        weather.get("condition"),

        air.get("aqi"),
        air.get("co"),
        air.get("no"),
        air.get("no2"),
        air.get("o3"),
        air.get("so2"),
        air.get("pm2_5"),
        air.get("pm10"),
        air.get("nh3"),

        data.get("timestamp")
    ]

    folha_dadus.append(linha)


# ============================================================
# AJUSTA LARGURA KOLUNA
# ============================================================

for column in folha_dadus.columns:

    largura = 0

    for cell in column:

        valor = str(cell.value) if cell.value is not None else ""

        if len(valor) > largura:
            largura = len(valor)

    largura = min(largura + 2, 30)

    folha_dadus.column_dimensions[
        column[0].column_letter
    ].width = largura


folha_dadus.freeze_panes = "A2"


# ============================================================
# FOLHA 2 — RESUMU
# ============================================================

total_dadus = len(dadus)

meta_dadus = 10000

progresu = (total_dadus / meta_dadus) * 100

lokasaun = sorted(
    set(
        data.get("location")
        for data in dadus
        if data.get("location")
    )
)

folha_resumu["A1"] = "WEATHER & AIR QUALITY MONITORING"
folha_resumu["A2"] = "🇹🇱 TIMOR-LESTE"

folha_resumu["A4"] = "Informasaun"
folha_resumu["B4"] = "Valor"

folha_resumu["A5"] = "Total Dadus"
folha_resumu["B5"] = total_dadus

folha_resumu["A6"] = "Meta Dadus"
folha_resumu["B6"] = meta_dadus

folha_resumu["A7"] = "Progresu"
folha_resumu["B7"] = f"{progresu:.2f}%"

folha_resumu["A8"] = "Total Fatin"
folha_resumu["B8"] = len(lokasaun)

folha_resumu["A9"] = "Fatin sira"
folha_resumu["B9"] = ", ".join(lokasaun)

folha_resumu["A10"] = "Relatoriu Kria"
folha_resumu["B10"] = datetime.now().strftime(
    "%Y-%m-%d %H:%M:%S"
)

for cell in folha_resumu[4]:
    cell.font = Font(bold=True)

folha_resumu["A1"].font = Font(
    bold=True,
    size=16
)

folha_resumu["A2"].font = Font(
    bold=True,
    size=12
)

folha_resumu.column_dimensions["A"].width = 25
folha_resumu.column_dimensions["B"].width = 70


# ============================================================
# FOLHA 3 — STATISTIK
# ============================================================

folha_statistik["A1"] = "STATISTIKA DADUS"
folha_statistik["A1"].font = Font(
    bold=True,
    size=16
)

folha_statistik["A3"] = "Parametru"
folha_statistik["B3"] = "Minimu"
folha_statistik["C3"] = "Maksimu"
folha_statistik["D3"] = "Média"

for cell in folha_statistik[3]:
    cell.font = Font(bold=True)


def valores_parametru(naran_weather, naran_air):

    valores = []

    for data in dadus:

        weather = data.get("weather", {})
        air = data.get("air_quality", {})

        if naran_weather:
            valor = weather.get(naran_weather)
        else:
            valor = air.get(naran_air)

        if isinstance(valor, (int, float)):
            valores.append(valor)

    return valores


parametrus = [
    ("Temperatura", "temperature", None),
    ("Umidade", "humidity", None),
    ("Pressaun", "pressure", None),
    ("Anin", "wind_speed", None),
    ("AQI", None, "aqi"),
    ("PM2.5", None, "pm2_5"),
    ("PM10", None, "pm10"),
]

linha = 4

for naran, weather_key, air_key in parametrus:

    valores = valores_parametru(
        weather_key,
        air_key
    )

    if valores:

        folha_statistik.cell(
            linha,
            1,
            naran
        )

        folha_statistik.cell(
            linha,
            2,
            min(valores)
        )

        folha_statistik.cell(
            linha,
            3,
            max(valores)
        )

        folha_statistik.cell(
            linha,
            4,
            sum(valores) / len(valores)
        )

        linha += 1


folha_statistik.column_dimensions["A"].width = 20
folha_statistik.column_dimensions["B"].width = 15
folha_statistik.column_dimensions["C"].width = 15
folha_statistik.column_dimensions["D"].width = 15


# ============================================================
# SALVA RELATORIU
# ============================================================

workbook.save(ARQUIVU_EXCEL)

print()
print("=" * 60)
print("📊 RELATORIU EXCEL KRIA HO SUSSESU! ✅")
print("=" * 60)
print(f"📄 Arquivu : {ARQUIVU_EXCEL}")
print(f"💾 Total Dadus : {total_dadus}")
print(f"🎯 Meta Dadus  : {meta_dadus}")
print(f"📈 Progresu    : {progresu:.2f}%")
print("=" * 60)

client.close()