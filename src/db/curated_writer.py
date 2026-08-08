"""
Module dùng CHUNG để ghi / cập nhật dữ liệu thời tiết vào tầng Curated (SQLite).

Trước đây `load_to_curated.py` ghi vào bảng `weather_forecast` (replace toàn bộ)
còn `run_incremental.py` ghi vào bảng `weather_hourly` (append + dedup bằng pandas).
Hai luồng lệch nhau khiến Dashboard (chỉ đọc `weather_hourly`) không bao giờ thấy
dữ liệu do `load_to_curated.py` nạp vào.

Module này thống nhất lại thành MỘT bảng duy nhất (`weather_hourly`), MỘT schema
chuẩn, và MỘT hàm ghi (`upsert_weather_data`) mà mọi pipeline đều phải gọi qua đây.
Việc chống trùng lặp được đẩy xuống tầng DB bằng PRIMARY KEY hợp phần
(city_code, timestamp) thay vì chỉ dựa vào `drop_duplicates()` phía pandas.
"""
import logging
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CURATED_DIR = ROOT_DIR / "data" / "3_curated"
DB_PATH = CURATED_DIR / "weather.db"

TABLE_NAME = "weather_hourly"

# Schema chuẩn hoá — mọi DataFrame trước khi ghi vào Curated đều phải map đúng các cột này.
# transform_historical.transform_weather_json() đã trả về đúng thứ tự cột này.
SCHEMA_COLUMNS = [
    "city_code",
    "timestamp",
    "latitude",
    "longitude",
    "temperature",
    "humidity",
    "precipitation",
    "wind_speed",
]

PK_COLUMNS = ["city_code", "timestamp"]


def _ensure_table(conn: sqlite3.Connection) -> None:
    """Tạo bảng weather_hourly nếu chưa tồn tại, với PRIMARY KEY hợp phần
    (city_code, timestamp) — SQLite tự chống trùng lặp ở tầng DB, không còn
    phụ thuộc hoàn toàn vào logic dedup ở tầng ứng dụng."""
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            city_code     TEXT NOT NULL,
            timestamp     TEXT NOT NULL,
            latitude      REAL,
            longitude     REAL,
            temperature   REAL,
            humidity      REAL,
            precipitation REAL,
            wind_speed    REAL,
            PRIMARY KEY (city_code, timestamp)
        )
        """
    )
    conn.commit()


def get_max_timestamp(city_code: Optional[str] = None) -> Optional[str]:
    """Trả về mốc timestamp mới nhất hiện có trong DB.

    Nếu truyền city_code, chỉ lấy mốc riêng của thành phố đó — quan trọng vì
    các thành phố có thể có độ trễ dữ liệu khác nhau (một thành phố mới thêm
    vào CITIES sẽ không bị "nhảy cóc" theo mốc MAX toàn cục của thành phố khác).
    """
    if not DB_PATH.exists():
        return None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            tables = pd.read_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                conn,
                params=(TABLE_NAME,),
            )
            if tables.empty:
                return None

            if city_code:
                df = pd.read_sql(
                    f"SELECT MAX(timestamp) as max_ts FROM {TABLE_NAME} WHERE city_code = ?",
                    conn,
                    params=(city_code,),
                )
            else:
                df = pd.read_sql(f"SELECT MAX(timestamp) as max_ts FROM {TABLE_NAME}", conn)

            return df["max_ts"].iloc[0] if not df.empty else None
    except Exception as e:
        logging.warning(f"⚠️ Chưa lấy được MAX(timestamp) từ DB: {e}")
        return None


def upsert_weather_data(df: pd.DataFrame) -> int:
    """Upsert (INSERT OR REPLACE) một DataFrame vào bảng `weather_hourly`.

    Đây là hàm DUY NHẤT được phép ghi vào tầng Curated. Cả batch pipeline
    (`load_to_curated.py`) lẫn incremental pipeline (`run_incremental.py`)
    đều gọi qua đây, đảm bảo dùng chung 1 bảng, 1 schema, 1 cơ chế chống trùng
    — dù pipeline nào chạy trước/sau/song song, dữ liệu vẫn nhất quán.

    Trả về số dòng đã upsert.
    """
    if df.empty:
        logging.warning("⚠️ DataFrame rỗng, không có gì để ghi vào Curated.")
        return 0

    missing_cols = [c for c in SCHEMA_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"❌ DataFrame thiếu các cột bắt buộc theo schema chuẩn: {missing_cols}"
        )

    df = df[SCHEMA_COLUMNS].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"]).astype(str)

    # Dedup nội bộ batch trước khi ghi (phòng trường hợp file nguồn tự trùng)
    df = df.drop_duplicates(subset=PK_COLUMNS, keep="last")

    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_table(conn)
        rows = list(df.itertuples(index=False, name=None))
        placeholders = ", ".join(["?"] * len(SCHEMA_COLUMNS))
        conn.executemany(
            f"INSERT OR REPLACE INTO {TABLE_NAME} ({', '.join(SCHEMA_COLUMNS)}) "
            f"VALUES ({placeholders})",
            rows,
        )
        conn.commit()

    logging.info(f"✅ Đã upsert {len(df)} dòng vào bảng `{TABLE_NAME}` ({DB_PATH.name}).")
    return len(df)
