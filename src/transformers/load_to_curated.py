import logging
import sys
from pathlib import Path

import pandas as pd

# Cấu hình đường dẫn để Python tìm thấy thư mục gốc của dự án
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

# Trước đây file này tự mở kết nối sqlite3 và ghi vào bảng `weather_forecast`
# bằng if_exists="replace" — HOÀN TOÀN tách biệt với bảng `weather_hourly` mà
# run_incremental.py và dashboard sử dụng. Kết quả: dữ liệu batch nạp vào đây
# không bao giờ hiện lên Dashboard. Giờ dùng chung writer để về đúng 1 bảng.
from src.db.curated_writer import upsert_weather_data

# Cấu hình logging chuyên nghiệp
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Khai báo đường dẫn động theo chuẩn Project DE1
CLEANSED_DIR = ROOT_DIR / "data" / "2_cleansed"


def load_parquet_to_sqlite():
    """Đọc toàn bộ file .parquet trong 2_cleansed và UPSERT vào bảng
    `weather_hourly` ở tầng 3_curated (dùng chung writer với run_incremental.py)."""
    # 1. Tìm tất cả các file .parquet trong thư mục 2_cleansed
    parquet_files = list(CLEANSED_DIR.glob("*.parquet"))

    if not parquet_files:
        logging.warning("⚠️ Không tìm thấy file .parquet nào trong thư mục 2_cleansed!")
        return

    logging.info(
        f"🚀 Bắt đầu nạp dữ liệu từ {len(parquet_files)} file Parquet vào SQLite DB..."
    )

    # 2. Đọc và hợp nhất (concat) tất cả file parquet thành 1 DataFrame duy nhất
    dfs = []
    for p_file in parquet_files:
        try:
            df = pd.read_parquet(p_file)
            dfs.append(df)
            logging.info(f"📄 Đã đọc: {p_file.name} ({len(df)} dòng)")
        except Exception as e:
            logging.error(f"❌ Lỗi khi đọc file {p_file.name}: {e}")

    if not dfs:
        logging.error("❌ Không có dữ liệu hợp lệ nào được đọc từ tầng cleansed!")
        return

    full_df = pd.concat(dfs, ignore_index=True)

    # 3. Upsert vào Curated qua writer chung — chống trùng bằng PRIMARY KEY
    #    (city_code, timestamp) ở tầng DB, không cần tự drop_duplicates thủ công nữa.
    try:
        n = upsert_weather_data(full_df)
        logging.info(f"🎉 Hoàn thành! Đã upsert {n} dòng vào tầng Curated.")
        logging.info(f"📍 Đường dẫn Database: {ROOT_DIR / 'data' / '3_curated' / 'weather.db'}")
    except Exception as e:
        logging.error(f"❌ Lỗi khi ghi dữ liệu vào SQLite: {e}")


if __name__ == "__main__":
    load_parquet_to_sqlite()
