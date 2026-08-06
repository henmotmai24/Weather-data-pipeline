import json
import logging
import sys
from pathlib import Path

import requests

# 1. Cấu hình đường dẫn để Python tìm thấy thư mục gốc của dự án
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

# Import danh sách thành phố  vừa tạo
from src.config.cities import CITIES

# Cấu hình hiển thị nhật ký (Log)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Đường dẫn API thời tiết lịch sử của Open-Meteo
HISTORICAL_API_URL = "https://archive-api.open-meteo.com/v1/archive"

# Thư mục lưu dữ liệu thô (Tầng 1_landing)
LANDING_DIR = ROOT_DIR / "data" / "1_landing"


def fetch_weather_history(city_info: dict, start_date: str, end_date: str):
    """Hàm gửi request lên API để lấy dữ liệu thời tiết của 1 thành phố"""
    params = {
        "latitude": city_info["lat"],
        "longitude": city_info["lon"],
        "start_date": start_date,
        "end_date": end_date,
        # Các chỉ số  muốn lấy
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "timezone": "UTC",
    }

    try:
        response = requests.get(HISTORICAL_API_URL, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(
                f"Lỗi khi lấy dữ liệu {city_info['city_code']}: Status {response.status_code}"
            )
            return None
    except Exception as e:
        logging.error(f"Gặp sự cố kết nối với {city_info['city_code']}: {e}")
        return None


def main():
    # Tạo thư mục 1_landing nếu chưa có
    LANDING_DIR.mkdir(parents=True, exist_ok=True)

    # Thiết lập khoảng thời gian lịch sử (10 năm: 2016 -> 2026)
    START_DATE = "2016-01-01"
    END_DATE = "2026-07-01"

    logging.info(
        f"🚀 Bắt đầu cào dữ liệu lịch sử ({START_DATE} -> {END_DATE}) cho {len(CITIES)} thành phố..."
    )

    for city in CITIES:
        city_code = city["city_code"]
        logging.info(f"⏳ Đang tải dữ liệu cho thành phố: {city_code}...")

        # Gọi API lấy dữ liệu
        raw_data = fetch_weather_history(city, START_DATE, END_DATE)

        if raw_data:
            # Lưu file JSON thô vào data/1_landing/
            output_file = LANDING_DIR / f"{city_code}_raw.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)

            logging.info(f"✅ Đã lưu dữ liệu thô thành công: {output_file.name}")

    logging.info("🎉 Hoàn thành tầng Extraction (Tải dữ liệu thô vào 1_landing)!")


if __name__ == "__main__":
    main()
