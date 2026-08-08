import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

# --- TÁI SỬ DỤNG logic đã có, thay vì viết lại (bản cũ tự gọi requests.get(),
#     tự parse JSON, tự nạp thẳng vào SQLite — trùng lặp và LỆCH SCHEMA so với
#     pipeline batch: thiếu cột precipitation/latitude/longitude, và dùng
#     CITIES tự khai báo riêng thay vì import từ config) ---
from src.config.cities import CITIES
from src.extractors.extract_historical import fetch_weather_history, save_raw_json
from src.transformers.transform_historical import transform_weather_json
from src.db.curated_writer import get_max_timestamp, upsert_weather_data

# Cấu hình logging chuyên nghiệp
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Mốc mặc định khi 1 thành phố chưa có dữ liệu gì trong DB (VD thành phố mới thêm vào CITIES)
DEFAULT_BACKFILL_START = "2016-01-01"


def run_catchup_pipeline():
    """Pipeline Dynamic Catch-Up — đi đúng 3 tầng Medallion:

        Extract (1_landing) -> Transform (2_cleansed logic) -> Load (3_curated)

    thay vì gọi thẳng API rồi ghi trực tiếp vào SQLite như bản cũ. Nhờ tái sử
    dụng `fetch_weather_history` / `transform_weather_json` / `upsert_weather_data`,
    schema và bảng đích luôn nhất quán với pipeline batch lịch sử.

    Mốc catch-up được tính RIÊNG cho từng thành phố (không dùng 1 mốc MAX chung),
    để tránh 1 thành phố mới thêm vào CITIES bị "nhảy cóc" theo mốc của thành phố khác.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    total_rows = 0

    for city in CITIES:
        city_code = city["city_code"]

        # 1. Xác định mốc bắt đầu cào bù cho riêng thành phố này
        max_ts = get_max_timestamp(city_code=city_code)
        if max_ts:
            start_date = str(max_ts)[:10]
            logging.info(f"📌 [{city_code}] Mốc dữ liệu mới nhất trong DB: {max_ts}")
        else:
            start_date = DEFAULT_BACKFILL_START
            logging.info(
                f"📌 [{city_code}] DB chưa có dữ liệu, cào bù từ mặc định: {start_date}"
            )

        if start_date >= today_str:
            logging.info(f"✅ [{city_code}] Dữ liệu đã cập nhật đến hiện tại, bỏ qua.")
            continue

        logging.info(f"🚀 [{city_code}] Catch-Up từ [{start_date}] đến [{today_str}]...")

        # 2. EXTRACT: cào dữ liệu thô & lưu vào 1_landing
        raw_data = fetch_weather_history(city, start_date, today_str)
        if not raw_data:
            logging.warning(f"⚠️ [{city_code}] Không cào được dữ liệu mới, bỏ qua.")
            continue
        json_path = save_raw_json(city_code, raw_data)

        # 3. TRANSFORM: làm sạch dữ liệu thô thành DataFrame chuẩn schema
        try:
            df_cleansed = transform_weather_json(json_path)
        except Exception as e:
            logging.error(f"❌ [{city_code}] Lỗi khi transform dữ liệu: {e}")
            continue

        # 4. LOAD: upsert vào Curated — PRIMARY KEY (city_code, timestamp) tự chống trùng
        try:
            n = upsert_weather_data(df_cleansed)
            total_rows += n
            logging.info(f"  └─ 📄 [{city_code}] Đã upsert {n} dòng dữ liệu mới")
        except Exception as e:
            logging.error(f"❌ [{city_code}] Lỗi khi ghi vào Curated: {e}")

    logging.info(
        f"🎉 Hoàn thành Catch-Up Pipeline! Tổng cộng {total_rows} dòng đã được upsert."
    )


if __name__ == "__main__":
    run_catchup_pipeline()
