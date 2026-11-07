import os
from pymongo import MongoClient
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# MONGODB CONFIGURATION
# ============================================================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://admin:timor123@localhost:27017/?authSource=admin"
)

DATABASE_NAME = "weather_timor"

COLLECTION_NAME = "weather_air_quality"


# ============================================================
# CONNECT TO MONGODB
# ============================================================

try:

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )

    # Test koneksi MongoDB
    client.server_info()

    db = client[DATABASE_NAME]

    collection = db[COLLECTION_NAME]

    print("🍃 MongoDB konekta ho susesu! ✅")

except Exception as error:

    print(f"❌ MongoDB la konsege konekta: {error}")

    client = None


# ============================================================
# SAVE DATA TO MONGODB
# ============================================================

def save_data(data):

    try:

        if client is None:

            print("❌ MongoDB seidauk konekta.")

            return False


        result = collection.insert_one(
            data
        )


        print(
            f"💾 Dadus {data['location']} "
            f"rai ona iha MongoDB! ✅"
        )


        return result.inserted_id


    except Exception as error:

        print(
            f"❌ Error rai dadus MongoDB: "
            f"{error}"
        )

        return False