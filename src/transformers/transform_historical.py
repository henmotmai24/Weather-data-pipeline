import logging
from pathlib import Path
import pandas as pd

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Khai báo đường dẫn
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
LANDING_DIR = ROOT_DIR / "data" / "1_landing"
CLEANSED_DIR = ROOT_DIR / "data" / "2_cleansed"


def transform_weather_json(json_path: Path) -> pd.DataFrame:
    """Đọc file JSON thô, flatten dữ liệu và chuyển đổi thành Pandas DataFrame"""
    # 1. Đọc file JSON thô bằng Pandas
    df_raw = pd.read_json(json_path)

    # 2. Bóc tách dữ liệu lồng nhau trong trường 'hourly'
    hourly_data = df_raw["hourly"]

    # 3. Tạo DataFrame dạng bảng từ dictionary hourly
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(hourly_data["time"]),
            "temperature": hourly_data["temperature_2m"],
            "humidity": hourly_data["relative_humidity_2m"],
            "precipitation": hourly_data["precipitation"],
            "wind_speed": hourly_data["wind_speed_10m"],
        }
    )

    # 4. Trích xuất thông tin thành phố & tọa độ làm metadata
    df["city_code"] = json_path.stem.replace("_raw", "")
    df["latitude"] = df_raw["latitude"].iloc[0]
    df["longitude"] = df_raw["longitude"].iloc[0]

    # 5. Sắp xếp lại thứ tự các cột cho gọn gàng
    columns_order = [
        "city_code",
        "timestamp",
        "latitude",
        "longitude",
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed",
    ]
    return df[columns_order]


def main():
    CLEANSED_DIR.mkdir(parents=True, exist_ok=True)

    # Tìm tất cả file *_raw.json trong thư mục 1_landing
    raw_files = list(LANDING_DIR.glob("*_raw.json"))

    if not raw_files:
        logging.warning("⚠️ Không tìm thấy file JSON nào trong 1_landing!")
        return

    logging.info(f"🚀 Bắt đầu chuyển đổi {len(raw_files)} file dữ liệu thô...")

    for file_path in raw_files:
        try:
            city_code = file_path.stem.replace("_raw", "")
            logging.info(f"⏳ Đang xử lý làm sạch dữ liệu cho: {city_code}...")

            # Chuyển đổi JSON -> DataFrame
            df_cleansed = transform_weather_json(file_path)

            # Lưu file dưới dạng Parquet vào 2_cleansed/
            output_parquet = CLEANSED_DIR / f"{city_code}_cleansed.parquet"
            df_cleansed.to_parquet(output_parquet, index=False)

            logging.info(
                f"✅ Đã lưu file Parquet thành công: {output_parquet.name} ({len(df_cleansed)} dòng)"
            )

        except Exception as e:
            logging.error(f"❌ Lỗi khi xử lý file {file_path.name}: {e}")

    logging.info("🎉 Hoàn thành tầng Transformation (Lưu file Parquet vào 2_cleansed)!")


if __name__ == "__main__":
    main()
