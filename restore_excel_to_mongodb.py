
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from openpyxl import load_workbook
from pymongo import MongoClient, UpdateOne


# ============================================================
# KONFIGURASAUN
# ============================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

EXCEL_FILE = BASE_DIR / "weather_timor_report.xlsx"

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "weather_timor"
COLLECTION_NAME = "weather_air_quality"

BATCH_SIZE = 500


# ============================================================
# FUNSAUN AUXILIAR
# ============================================================

def konverte_numeru(value):
    if value is None or value == "":
        return None

    if isinstance(value, (int, float)):
        number = float(value)
    else:
        number = float(str(value).strip())

    if number.is_integer():
        return int(number)

    return number


def lee_dadus_excel():
    workbook = load_workbook(
        EXCEL_FILE,
        read_only=True,
        data_only=True
    )

    sheet = workbook["Dadus"]

    headers = next(
        sheet.iter_rows(min_row=1, max_row=1, values_only=True)
    )

    expected_headers = [
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

    if list(headers) != expected_headers:
        workbook.close()
        raise ValueError(
            "Estrutura koluna Excel la hanesan ho estrutura ne'ebe espera."
        )

    dadus_uniku = {}
    invalid_rows = 0
    duplicate_rows = 0

    for row in sheet.iter_rows(min_row=2, values_only=True):

        if not row or not row[0] or not row[18]:
            invalid_rows += 1
            continue

        try:
            location = str(row[0]).strip()

            timestamp = row[18]

            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()
            else:
                timestamp = str(timestamp).strip()

            document = {
                "location": location,
                "latitude": konverte_numeru(row[1]),
                "longitude": konverte_numeru(row[2]),

                "weather": {
                    "temperature": konverte_numeru(row[3]),
                    "humidity": konverte_numeru(row[4]),
                    "pressure": konverte_numeru(row[5]),
                    "wind_speed": konverte_numeru(row[6]),
                    "rain": konverte_numeru(row[7]),
                    "condition": row[8]
                },

                "air_quality": {
                    "aqi": konverte_numeru(row[9]),
                    "co": konverte_numeru(row[10]),
                    "no": konverte_numeru(row[11]),
                    "no2": konverte_numeru(row[12]),
                    "o3": konverte_numeru(row[13]),
                    "so2": konverte_numeru(row[14]),
                    "pm2_5": konverte_numeru(row[15]),
                    "pm10": konverte_numeru(row[16]),
                    "nh3": konverte_numeru(row[17])
                },

                "timestamp": timestamp
            }

            key = (location, timestamp)

            if key in dadus_uniku:
                duplicate_rows += 1

            dadus_uniku[key] = document

        except (ValueError, TypeError, IndexError):
            invalid_rows += 1

    workbook.close()

    return list(dadus_uniku.values()), invalid_rows, duplicate_rows


# ============================================================
# IMPORTA DADUS BA MONGODB
# ============================================================

def main():

    print("=" * 55)
    print("RESTAURASAUN DADUS WEATHER TIMOR-LESTE")
    print("=" * 55)

    if not MONGO_URI:
        raise ValueError(
            "MONGO_URI la hetan iha ficheiru .env."
        )

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Excel la hetan: {EXCEL_FILE}"
        )

    print("\n📂 Lee dadus husi Excel...")

    records, invalid, duplicates = lee_dadus_excel()

    print(f"📊 Dadus Excel validu : {len(records)}")
    print(f"⚠️ Dadus invalidu     : {invalid}")
    print(f"🔁 Dadus repetidu     : {duplicates}")

    print("\n🔌 Koneksaun ba MongoDB...")

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000
    )

    client.admin.command("ping")

    collection = client[DATABASE_NAME][COLLECTION_NAME]

    before_count = collection.count_documents({})

    print(f"🍃 Dadus antes importasaun: {before_count}")

    print("\n📥 Hahu importasaun...")

    inserted_total = 0
    existing_total = 0

    for start in range(0, len(records), BATCH_SIZE):

        batch = records[start:start + BATCH_SIZE]

        operations = []

        for document in batch:

            operations.append(
                UpdateOne(
                    {
                        "location": document["location"],
                        "timestamp": document["timestamp"]
                    },
                    {
                        "$setOnInsert": document
                    },
                    upsert=True
                )
            )

        result = collection.bulk_write(
            operations,
            ordered=False
        )

        inserted_total += result.upserted_count
        existing_total += result.matched_count

        print(
            f"✅ Progresu: {min(start + BATCH_SIZE, len(records))}"
            f"/{len(records)}"
        )

    after_count = collection.count_documents({})

    print("\n" + "=" * 55)
    print("REZULTADU IMPORTASAUN")
    print("=" * 55)

    print(f"📦 Dadus antes       : {before_count}")
    print(f"📥 Dadus foun        : {inserted_total}")
    print(f"🔁 Dadus existente   : {existing_total}")
    print(f"🍃 Total agora       : {after_count}")
    print(f"📄 Dadus Excel       : {len(records)}")

    print("\n✅ IMPORTASAUN REMATA!")

    client.close()


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print("\n❌ Sala durante importasaun:")
        print(error)
        raise
