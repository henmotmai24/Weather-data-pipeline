import glob
import logging
from pathlib import Path
import sqlite3
import pandas as pd

# Cấu hình logging chuyên nghiệp
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Khai báo đường dẫn động theo chuẩn Project DE1
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLEANSED_DIR = ROOT_DIR / "data" / "2_cleansed"
CURATED_DIR = ROOT_DIR / "data" / "3_curated"
DB_PATH = CURATED_DIR / "weather.db"


def load_parquet_to_sqlite():
    """Đọc toàn bộ file .parquet trong 2_cleansed và ghi vào SQLite Database ở 3_curated"""
    # 1. Đảm bảo thư mục 3_curated đã tồn tại
    CURATED_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Tìm tất cả các file .parquet trong thư mục 2_cleansed
    parquet_files = list(CLEANSED_DIR.glob("*.parquet"))

    if not parquet_files:
        logging.warning("⚠️ Không tìm thấy file .parquet nào trong thư mục 2_cleansed!")
        return

    logging.info(
        f"🚀 Bắt đầu nạp dữ liệu từ {len(parquet_files)} file Parquet vào SQLite DB..."
    )

    # 3. Đọc và hợp nhất (concat) tất cả file parquet thành 1 DataFrame duy nhất
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

    # 4. Tự động loại bỏ các bản ghi trùng lặp (nếu có) dựa trên city_code và timestamp
    dedup_cols = ["city_code", "timestamp"]
    if all(col in full_df.columns for col in dedup_cols):
        before_len = len(full_df)
        full_df = full_df.drop_duplicates(subset=dedup_cols, keep="last")
        after_len = len(full_df)
        if before_len > after_len:
            logging.info(f"🧹 Đã loại bỏ {before_len - after_len} dòng trùng lặp.")

    # 5. Kết nối SQLite và ghi vào Bảng 'weather_forecast'
    try:
        conn = sqlite3.connect(DB_PATH)

        # if_exists='replace': Ghi đè lại bảng dữ liệu mới nhất (hoặc chọn 'append' nếu muốn cộng dồn)
        full_df.to_sql("weather_forecast", conn, if_exists="replace", index=False)

        conn.close()

        logging.info(f"✅ Đã ghi thành công {len(full_df)} dòng vào SQLite DB!")
        logging.info(f"📍 Đường dẫn Database: {DB_PATH}")

    except Exception as e:
        logging.error(f"❌ Lỗi khi ghi dữ liệu vào SQLite: {e}")


if __name__ == "__main__":
    load_parquet_to_sqlite()
