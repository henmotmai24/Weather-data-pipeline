import sys
from pathlib import Path

# Thêm thư mục gốc của dự án vào đường dẫn tìm kiếm của Python
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import logging
import pandas as pd
from src.extractors.extract_weather import LATITUDE, LONGITUDE, extract_weather_data

# ... (Các đoạn code bên dưới giữ nguyên) ...
import logging
import pandas as pd
from src.extractors.extract_weather import LATITUDE, LONGITUDE, extract_weather_data

# Bật logging để theo dõi từng bước
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def transform_weather_data(raw_json: dict) -> pd.DataFrame:
    hourly_data = raw_json.get("hourly", {})
    df = pd.DataFrame(hourly_data)

    column_mapping = {
        "time": "datetime",
        "temperature_2m": "temp_c",
        "relative_humidity_2m": "humidity_pct",
        "wind_speed_10m": "wind_speed_kmh",
    }

    df = df[list(column_mapping.keys())].rename(columns=column_mapping)
    df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize("Asia/Ho_Chi_Minh")
    df["city"] = "Ho_Chi_Minh"
    return df


# --- ĐOẠN LỆNH BẮT BUỘC ĐỂ IN KẾT QUẢ ---
print("\n>>> ĐANG BẮT ĐẦU CHẠY PIPELINE TRANSFORM...\n")

# 1. Kéo dữ liệu thô từ API
raw_data = extract_weather_data(LATITUDE, LONGITUDE)

# 2. Làm sạch thành DataFrame
clean_df = transform_weather_data(raw_data)

# 3. In kết quả ra Terminal
print("\n" + "=" * 20 + " KẾT QUẢ BẢNG DATAFRAME " + "=" * 20)
print(clean_df.head(10))  # In 10 dòng đầu
print("=" * 64 + "\n")
