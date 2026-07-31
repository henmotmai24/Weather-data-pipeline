import sys
from pathlib import Path

# Cấu hình đường dẫn thư mục gốc dự án
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

import logging
import sqlite3
import pandas as pd

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Đường dẫn file Database SQLite (sẽ được tạo tự động tại thư mục data/3_curated)
DB_PATH = ROOT_DIR / "data" / "3_curated" / "weather_data.db"


def load_to_sqlite(df: pd.DataFrame, table_name: str = "daily_weather") -> None:
    """
    Lưu trữ DataFrame vào Cơ sở dữ liệu SQLite.
    - if_exists='append': Thêm dữ liệu mới vào bảng (hoặc tạo mới bảng nếu chưa tồn tại).
    - index=False: Không lưu cột chỉ số (Index) của Pandas vào Database.
    """
    logging.info(f"Bắt đầu quá trình Load dữ liệu vào Database: {DB_PATH.name}...")

    # Đảm bảo thư mục lưu Database tồn tại
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Mở kết nối tới SQLite Database (Nếu file .db chưa có, SQLite sẽ tự động khởi tạo)
    with sqlite3.connect(DB_PATH) as conn:
        # Dùng Pandas to_sql để tự động tạo bảng & chèn dữ liệu
        df.to_sql(name=table_name, con=conn, if_exists="append", index=False)

    logging.info(
        f"Lưu thành công {len(df)} dòng dữ liệu vào bảng '{table_name}' trong SQLite!"
    )


# --- TEST CHẠY TOÀN BỘ PIPELINE ETL ---
if __name__ == "__main__":
    from src.extractors.extract_weather import LATITUDE, LONGITUDE, extract_weather_data
    from src.transformers.transform_weather import transform_weather_data

    print("\n>>> BẮT ĐẦU CHẠY PIPELINE ETL HOÀN CHỈNH...\n")

    # 1. EXTRACT
    raw_json = extract_weather_data(LATITUDE, LONGITUDE)

    # 2. TRANSFORM
    clean_df = transform_weather_data(raw_json)

    # 3. LOAD
    load_to_sqlite(clean_df, table_name="hourly_weather")

    print("\n>>> HOÀN THÀNH PIPELINE ETL!")
