import json
import logging
import requests

# Cấu hình logging để theo dõi tiến trình
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# 1. Tọa độ địa lý
# TP.HCM: latitude = 10.8231, longitude = 106.6297
# (Nếu muốn dùng Hà Nội: latitude = 21.0285, longitude = 105.8542)
LATITUDE = 10.8231
LONGITUDE = 106.6297

# 2. Endpoint API Open-Meteo
BASE_URL = "https://api.open-meteo.com/v1/forecast"


def extract_weather_data(lat: float, lon: float) -> dict:
    """Gửi GET request tới Open-Meteo API để trích xuất dữ liệu thời tiết theo giờ."""
    # Khai báo các tham số truy vấn (Query Parameters)
    params = {
        "latitude": lat,
        "longitude": lon,
        # Các trường thông tin cần lấy theo giờ (hourly)
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "timezone": "Asia/Ho_Chi_Minh",
    }

    logging.info(f"Đang gửi request tới Open-Meteo API cho tọa độ ({lat}, {lon})...")

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)

        # Báo lỗi nếu kết nối không thành công (mã 4xx hoặc 5xx)
        response.raise_for_status()

        data = response.json()
        logging.info("Trích xuất dữ liệu thô (JSON) thành công!")
        return data

    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi khi trích xuất dữ liệu từ API: {e}")
        raise SystemExit(e)


def main():
    # Gọi hàm trích xuất
    weather_json = extract_weather_data(LATITUDE, LONGITUDE)

    # In dữ liệu thô (JSON) ra màn hình với định dạng thụt lùi (indent=2) cho dễ quan sát
    print("\n" + "=" * 30 + " DỮ LIỆU THÔ (RAW JSON) " + "=" * 30 + "\n")
    print(json.dumps(weather_json, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
