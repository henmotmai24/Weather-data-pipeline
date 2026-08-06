import sqlite3
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Cấu hình trang Dashboard
st.set_page_config(
    page_title="Weather Analytics - Project DE1",
    page_icon="🌤️",
    layout="wide",
)

# 2. Xử lý đường dẫn động tới Database ở tầng 3_curated
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT_DIR / "data" / "3_curated" / "weather.db"


@st.cache_data(ttl=10)  # Giảm ttl xuống 10 giây để refresh nhanh
def load_data():
    """Đọc dữ liệu mới nhất từ bảng weather_hourly trong SQLite DB"""
    if not DB_PATH.exists():
        st.warning(f"⚠️ File DB không tồn tại tại đường dẫn: {DB_PATH}")
        return pd.DataFrame()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Ưu tiên đọc từ bảng weather_hourly (bảng dữ liệu mới nhất)
            df = pd.read_sql(
                "SELECT * FROM weather_hourly ORDER BY timestamp ASC", conn
            )

            if not df.empty and "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df

    except Exception as e:
        st.error(f"❌ Lỗi khi đọc dữ liệu từ Database: {e}")
        return pd.DataFrame()


# 3. Giao diện chính của Dashboard
st.title("🌤️ Weather Analytics Dashboard — Project DE1")
st.caption("Dữ liệu trực quan hóa realtime từ SQLite Database (3_curated)")

df = load_data()

if df.empty:
    st.error(
        f"❌ Không tìm thấy dữ liệu tại `{DB_PATH}`. Hãy chắc chắn em đã chạy `load_to_curated.py`!"
    )
else:
    # --- SIDEBAR: Bộ lọc dữ liệu ---
    st.sidebar.header("🔍 Bộ lọc")
    city_list = df["city_code"].unique()
    selected_city = st.sidebar.selectbox("Chọn Thành phố:", city_list)

    # Lọc dữ liệu theo thành phố đã chọn
    city_df = df[df["city_code"] == selected_city].sort_values("timestamp")

    # --- TỔNG QUAN CHỈ SỐ (METRICS) ---
    st.subheader(f"📊 Chỉ số hiện tại: {selected_city.upper()}")
    col1, col2, col3, col4 = st.columns(4)

    latest_temp = city_df["temperature"].iloc[-1]
    avg_temp = city_df["temperature"].mean()
    avg_hum = city_df["humidity"].mean()
    max_wind = city_df["wind_speed"].max()

    col1.metric("Nhiệt độ mới nhất", f"{latest_temp:.1f} °C")
    col2.metric("Nhiệt độ TB", f"{avg_temp:.1f} °C")
    col3.metric("Độ ẩm TB", f"{avg_hum:.1f} %")
    col4.metric("Sức gió max", f"{max_wind:.1f} km/h")

    st.markdown("---")

    # --- ĐỒ THỊ TRỰC QUAN HÓA (PLOTLY) ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("🌡️ Biến động Nhiệt độ (°C)")
        fig_temp = px.line(
            city_df,
            x="timestamp",
            y="temperature",
            title=f"Nhiệt độ theo thời gian ({selected_city})",
            labels={
                "timestamp": "Thời gian",
                "temperature": "Nhiệt độ (°C)",
            },
            markers=True,
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    with chart_col2:
        st.subheader("💧 Biến động Độ ẩm (%)")
        fig_hum = px.line(
            city_df,
            x="timestamp",
            y="humidity",
            title=f"Độ ẩm theo thời gian ({selected_city})",
            labels={"timestamp": "Thời gian", "humidity": "Độ ẩm (%)"},
            markers=True,
        )
        st.plotly_chart(fig_hum, use_container_width=True)

    # --- BẢNG DỮ LIỆU CHI TIẾT ---
    with st.expander("👀 Xem bảng dữ liệu chi tiết"):
        st.dataframe(city_df, use_container_width=True)
