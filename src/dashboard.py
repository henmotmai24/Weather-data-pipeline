import sqlite3
from pathlib import Path

import plotly.express as px
import pandas as pd
import streamlit as st

# Đường dẫn tới Database
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "3_curated" / "weather_data.db"

# Cấu hình trang Streamlit
st.set_page_config(page_title="Weather Data Dashboard", page_icon="🌤️", layout="wide")

st.title("🌤️ Weather Data Pipeline Dashboard")
st.markdown(
    "Dữ liệu thời tiết được tự động trích xuất từ Open-Meteo API và lưu vào SQLite Database."
)


# Hàm đọc dữ liệu từ SQLite
def load_data():
    if not DB_PATH.exists():
        st.error("Chưa tìm thấy cơ sở dữ liệu! Vui lòng chạy Pipeline ETL trước.")
        return pd.DataFrame()

    with sqlite3.connect(DB_PATH) as conn:
        query = "SELECT * FROM hourly_weather"
        df = pd.read_sql_query(query, conn)
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df


df = load_data()

if not df.empty:
    # 1. Các chỉ số tổng quan (KPI Cards)
    st.subheader("📊 Thống kê nhanh")
    col1, col2, col3, col4 = st.columns(4)

    latest_temp = df["temp_c"].iloc[-1]
    max_temp = df["temp_c"].max()
    min_temp = df["temp_c"].min()
    avg_humidity = df["humidity_pct"].mean()

    col1.metric("Nhiệt độ hiện tại", f"{latest_temp} °C")
    col2.metric("Nhiệt độ cao nhất", f"{max_temp} °C")
    col3.metric("Nhiệt độ thấp nhất", f"{min_temp} °C")
    col4.metric("Độ ẩm trung bình", f"{avg_humidity:.1f} %")

    st.divider()

    # 2. Biểu đồ đường biến động nhiệt độ & độ ẩm
    st.subheader("📈 Biểu đồ biến động Nhiệt độ và Độ ẩm theo giờ")

    fig = px.line(
        df,
        x="datetime",
        y=["temp_c", "humidity_pct"],
        labels={"value": "Giá trị", "datetime": "Thời gian", "variable": "Thông số"},
        title="Nhiệt độ (°C) & Độ ẩm (%) Theo Thời Gian",
        markers=True,
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3. Hiển thị bảng dữ liệu thô trong Database
    with st.expander("🔍 Xem bảng dữ liệu thô trong Database"):
        st.dataframe(df.sort_values(by="datetime", ascending=False))
