import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import requests

# 1. Cấu hình đường dẫn để Python tìm thấy thư mục gốc của dự án
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

# Import danh sách thành phố — nguồn sự thật DUY NHẤT cho danh sách thành phố,
# mọi script khác (kể cả run_incremental.py) phải import từ đây, không tự khai báo lại.
from src.config.cities import CITIES

# Cấu hình hiển thị nhật ký (Log)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Đường dẫn API thời tiết lịch sử của Open-Meteo
HISTORICAL_API_URL = "https://archive-api.open-meteo.com/v1/archive"
REQUEST_TIMEOUT = 30

# Thư mục lưu dữ liệu thô (Tầng 1_landing)
LANDING_DIR = ROOT_DIR / "data" / "1_landing"


def fetch_weather_history(city_info: dict, start_date: str, end_date: str):
    """Gửi request lên Open-Meteo Archive API để lấy dữ liệu thời tiết của 1 thành phố.

    Hàm này được TÁI SỬ DỤNG bởi cả pipeline batch (extract_historical.main)
    lẫn pipeline incremental (run_incremental.py) — tránh việc 2 nơi tự viết
    lại logic gọi API với params khác nhau (trước đây run_incremental.py
    thiếu tham số `precipitation`, gây lệch schema so với batch)."""
    params = {
        "latitude": city_info["lat"],
        "longitude": city_info["lon"],
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "timezone": "UTC",
    }

    try:
        response = requests.get(HISTORICAL_API_URL, params=params, timeout=REQUEST_TIMEOUT)
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


def save_raw_json(city_code: str, raw_data: dict) -> Path:
    """Lưu dữ liệu thô vào tầng 1_landing (Landing Zone), trả về đường dẫn file đã lưu.
    Tách riêng thành hàm để run_incremental.py cũng đi qua đúng tầng Landing
    thay vì bỏ qua và nạp thẳng vào DB như trước."""
    LANDING_DIR.mkdir(parents=True, exist_ok=True)
    output_file = LANDING_DIR / f"{city_code}_raw.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    return output_file


def main():
    # Tạo thư mục 1_landing nếu chưa có
    LANDING_DIR.mkdir(parents=True, exist_ok=True)

    # Thiết lập khoảng thời gian lịch sử
    START_DATE = "2016-01-01"
    # Trước đây hardcode "2026-07-01" khiến script "hết hạn" theo thời gian thực.
    # Giờ luôn lấy đến ngày hiện tại để chạy đúng ở bất kỳ thời điểm nào.
    END_DATE = datetime.now().strftime("%Y-%m-%d")

    logging.info(
        f"🚀 Bắt đầu cào dữ liệu lịch sử ({START_DATE} -> {END_DATE}) cho {len(CITIES)} thành phố..."
    )

    for city in CITIES:
        city_code = city["city_code"]
        logging.info(f"⏳ Đang tải dữ liệu cho thành phố: {city_code}...")

        # Gọi API lấy dữ liệu
        raw_data = fetch_weather_history(city, START_DATE, END_DATE)

        if raw_data:
            output_file = save_raw_json(city_code, raw_data)
            logging.info(f"✅ Đã lưu dữ liệu thô thành công: {output_file.name}")

    logging.info("🎉 Hoàn thành tầng Extraction (Tải dữ liệu thô vào 1_landing)!")


if __name__ == "__main__":
    main()
