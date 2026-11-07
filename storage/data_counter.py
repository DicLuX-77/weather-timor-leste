import sys
import os


# ============================================================
# ATU ASESU BA FOLDER PROJETU
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, BASE_DIR)


# ============================================================
# IMPORT MONGODB STORAGE
# ============================================================

from storage.weather_storage import collection


# ============================================================
# KONTÁ TOTAL DADUS
# ============================================================

def count_data():

    try:

        total_data = collection.count_documents({})

        return total_data

    except Exception as error:

        print(
            f"❌ Error konta dadus: {error}"
        )

        return 0


# ============================================================
# HATUDU TOTAL DADUS
# ============================================================

if __name__ == "__main__":

    TARGET_DATA = 10000

    total_data = count_data()

    progress = (
        total_data / TARGET_DATA
    ) * 100


    print()

    print("📊 TOTAL DADUS MONGODB")

    print("=" * 50)

    print(
        f"💾 Total Dadus : {total_data}"
    )

    print(
        f"🎯 Meta Data  : {TARGET_DATA}"
    )

    print(
        f"📈 Progresu    : {progress:.2f}%"
    )

    print("=" * 50)