# 🌤️ End-to-End Automated Weather Data Pipeline (Medallion Architecture)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Architecture](https://img.shields.io/badge/Architecture-Medallion%20(3--Layer)-green)
![Database](https://img.shields.io/badge/Database-SQLite3-orange)
![Dashboard](https://img.shields.io/badge/Dashboard-Streamlit-red)

Dự án xây dựng hệ thống Data Pipeline tự động hóa từ đầu đến cuối (End-to-End) theo tiêu chuẩn **Medallion Architecture (Landing ➔ Cleansed ➔ Curated)**. Hệ thống thu thập, xử lý và làm sạch 26,000+ dòng dữ liệu thời tiết chuỗi thời gian cho 5 thành phố lớn, tự động phát hiện bù đắp khoảng trống dữ liệu (Self-Healing) và trực quan hóa trên Interactive Dashboard.

---

## 🏛️ Sơ đồ Kiến trúc Hệ thống (Architecture Diagram)

```text
                       [ Open-Meteo REST API ]
                                  │
                                  ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │ Layer 1: Landing Area (Raw Zone)                                │
 │ - Local Directory / JSON Format                                 │
 └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │ Layer 2: Cleansed Area (Silver Zone)                            │
 │ - CSV Format (Normalized Schema, Datetime Parsing, Drop Nulls)  │
 └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │ Layer 3: Curated Area (Gold Zone)                               │
 │ - SQLite Database (weather_hourly table)                        │
 └─────────────────────────────────────────────────────────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       [ Streamlit Dashboard ]         [ Scheduler Daemon ]
       (Realtime Analytics)            (Daily Auto Catch-Up)
```

---

## 🔥 Các Điểm Sáng Kỹ Thuật (Technical Highlights)

1. **Medallion Architecture (3 Tầng Dữ Liệu):**
   * **Landing (Raw):** Lưu trữ dữ liệu thô chuẩn format thu thập từ API.
   * **Cleansed (Silver):** Ép kiểu dữ liệu (Data Type Casting), chuẩn hóa thời gian, làm sạch dữ liệu khuyết thiếu.
   * **Curated (Gold):** Lưu trữ dữ liệu có cấu trúc tại SQLite Database sẵn sàng cho Analytics/BI.

2. **Incremental Load & Dynamic Catch-Up (Self-Healing Pipeline):**
   * Tự động truy vấn `MAX(timestamp)` trong SQLite Database để xác định mốc dữ liệu cuối cùng hiện có.
   * Tự động tính toán và cào bù (catch-up) khoảng hổng dữ liệu từ mốc cuối đến thời điểm hiện tại, đảm bảo **chuỗi thời gian liên tục 100% không bị gãy (Data Gap)**.

3. **Idempotency & Deduplication (Chống Trùng Lặp Dữ Liệu):**
   * Xử lý lọc trùng dữ liệu dựa trên khóa hợp phần `(city_code, timestamp)`, đảm bảo an toàn dữ liệu dù pipeline có bị khởi động lại nhiều lần.

4. **Automated Orchestration & Realtime Analytics:**
   * Sử dụng Daemon Scheduler tự động kích hoạt pipeline định kỳ.
   * Xây dựng Dashboard tương tác đa chiều bằng Streamlit và Plotly Express.

---

## 🛠️ Cấu trúc Thư mục Dự án (Project Structure)

```text
├── data/
│   ├── 1_landing/        # Dữ liệu thô cào từ API (JSON)
│   ├── 2_cleansed/       # Dữ liệu đã làm sạch (CSV)
│   └── 3_curated/        # Database đã sẵn sàng khai thác (SQLite)
├── src/
│   ├── pipelines/
│   │   └── run_incremental.py  # Script cào & nạp dữ liệu Incremental
│   ├── dashboard/
│   │   └── app.py              # Streamlit Analytics Dashboard
│   └── scheduler.py            # Bộ lập lịch tự động
├── requirements.txt            # Danh sách thư viện phụ thuộc
└── README.md                   # Tài liệu hướng dẫn kĩ thuật
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy (Getting Started)

### 1. Phân tách Môi trường & Cài đặt
```bash
# Clone dự án về máy
git clone <URL_REPOSITORY>
cd Project_DE1

# Khởi tạo môi trường ảo Python
python3 -m venv .venv
source .venv/bin/activate  # Trên Windows: .venv\Scripts\activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### 2. Chạy Pipeline Cào & Cập nhật Dữ liệu
```bash
python src/pipelines/run_incremental.py
```

### 3. Bật Dashboard Trực quan hóa
```bash
streamlit run src/dashboard/app.py
```

### 4. Bật Lập lịch Tự động
```bash
python src/scheduler.py
```
