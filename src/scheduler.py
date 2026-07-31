import sys
from pathlib import Path

# Cấu hình đường dẫn gốc
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import logging
import time
import schedule

# Import các bước ETL đã viết từ trước
from src.extractors.extract_weather import LATITUDE, LONGITUDE, extract_weather_data
from src.loaders.load_weather import load_to_sqlite
from src.transformers.transform_weather import transform_weather_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def run_etl_job():
    """Hàm chạy toàn bộ pipeline ETL"""
    logging.info("🚀 [AUTOMATION] Bắt đầu chạy Pipeline ETL tự động...")
    try:
        raw_data = extract_weather_data(LATITUDE, LONGITUDE)
        clean_df = transform_weather_data(raw_data)
        load_to_sqlite(clean_df, table_name="hourly_weather")
        logging.info("✅ [AUTOMATION] Pipeline ETL đã hoàn thành thành công!\n")
    except Exception as e:
        logging.error(f"❌ [AUTOMATION] Pipeline gặp lỗi: {e}\n")


def main():
    # 1. Chạy ngay 1 lần đầu tiên khi vừa bật script
    run_etl_job()

    # 2. Lập lịch tự động chạy vào 08:00 sáng mỗi ngày
    schedule.every().day.at("08:00").do(run_etl_job)

    # (Mẹo test nhanh: Bạn có thể bỏ comment dòng dưới để chạy mỗi 10 giây/lần xem thử)
    # schedule.every(10).seconds.do(run_etl_job)

    logging.info("⏰ Scheduler đang chạy ngầm... Nút Ctrl + C để dừng.")

    # Vòng lặp duy trì để lắng nghe sự kiện
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
