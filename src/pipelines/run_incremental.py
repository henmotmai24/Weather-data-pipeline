import logging
from datetime import datetime
from pathlib import Path
import sqlite3
import pandas as pd
import requests

# Cấu hình logging chuyên nghiệp
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Đường dẫn dự án
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT_DIR / "data" / "3_curated" / "weather.db"

# Tọa độ 5 thành phố trong dự án
CITIES = {
    "Ha_Noi": {"lat": 21.0285, "lon": 105.8542},
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "New_York": {"lat": 40.7128, "lon": -74.0060},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "Sydney": {"lat": -33.8688, "lon": 151.2093},
}


def get_max_timestamp() -> str | None:
    """Hỏi SQLite xem mốc thời gian mới nhất hiện có là ngày nào"""
    if not DB_PATH.exists():
        return None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Tự kiểm tra xem có bảng weather_hourly chưa?
            tables = pd.read_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='weather_hourly';",
                conn,
            )
            if tables.empty:
                return None

            df = pd.read_sql(
                "SELECT MAX(timestamp) as max_ts FROM weather_hourly", conn
            )
            return df["max_ts"].iloc[0] if not df.empty else None
    except Exception as e:
        logging.warning(f"Chưa lấy được MAX(timestamp) từ DB: {e}")
        return None


def fetch_city_weather(
    city_code: str, lat: float, lon: float, start_date: str, end_date: str
) -> pd.DataFrame:
    """Cào API Open-Meteo cho 1 thành phố từ start_date -> end_date"""
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}&"
        f"start_date={start_date}&end_date={end_date}&"
        f"hourly=temperature_2m,relative_humidity_2m,wind_speed_10m&"
        f"timezone=auto"
    )
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    data = response.json()

    hourly_data = data.get("hourly", {})
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(hourly_data.get("time", [])),
            "temperature": hourly_data.get("temperature_2m", []),
            "humidity": hourly_data.get("relative_humidity_2m", []),
            "wind_speed": hourly_data.get("wind_speed_10m", []),
            "city_code": city_code,
        }
    )


def run_catchup_pipeline():
    """Pipeline Dynamic Catch-Up tự động bù đắp khoảng trống dữ liệu"""
    # 1. Tự động xác định mốc thời gian cào bù
    max_ts = get_max_timestamp()
    today_str = datetime.now().strftime("%Y-%m-%d")

    if max_ts:
        latest_dt = pd.to_datetime(max_ts)
        start_date = latest_dt.strftime("%Y-%m-%d")
        logging.info(f"📌 Mốc dữ liệu mới nhất trong DB (MAX timestamp): {max_ts}")
    else:
        start_date = "2026-01-01"
        logging.info("📌 DB chưa có dữ liệu, đặt mặc định cào từ: 2026-01-01")

    logging.info(f"🚀 Bắt đầu Dynamic Catch-Up từ [{start_date}] đến [{today_str}]...")

    # 2. Cào dữ liệu cho cả 5 thành phố
    fetched_dfs = []
    for city_code, coords in CITIES.items():
        try:
            df_city = fetch_city_weather(
                city_code,
                coords["lat"],
                coords["lon"],
                start_date,
                today_str,
            )
            logging.info(
                f"  └─ 📄 Đã cào {len(df_city)} dòng dữ liệu mới cho {city_code}"
            )
            fetched_dfs.append(df_city)
        except Exception as e:
            logging.error(f"❌ Lỗi khi cào dữ liệu cho {city_code}: {e}")

    if not fetched_dfs:
        logging.warning("⚠️ Không cào thêm được dữ liệu nào.")
        return

    new_data_df = pd.concat(fetched_dfs, ignore_index=True)

    # 3. Kết hợp dữ liệu cũ & mới + Xử lý trùng lặp (Deduplication)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        try:
            existing_df = pd.read_sql("SELECT * FROM weather_hourly", conn)
            if not existing_df.empty:
                existing_df["timestamp"] = pd.to_datetime(existing_df["timestamp"])
                combined_df = pd.concat([existing_df, new_data_df], ignore_index=True)
            else:
                combined_df = new_data_df
        except Exception:
            combined_df = new_data_df

        # Loại bỏ các dòng trùng khớp cặp (city_code, timestamp)
        combined_df["timestamp"] = pd.to_datetime(combined_df["timestamp"])
        final_df = combined_df.drop_duplicates(
            subset=["city_code", "timestamp"]
        ).sort_values("timestamp")

        # Ghi đè lại bảng duy nhất weather_hourly với dữ liệu đã được làm sạch hoàn chỉnh
        final_df.to_sql("weather_hourly", conn, if_exists="replace", index=False)
        logging.info(
            f"✅ Đã ghi thành công! Tổng số dòng trong SQLite DB hiện tại: {len(final_df)} dòng."
        )


if __name__ == "__main__":
    run_catchup_pipeline()
