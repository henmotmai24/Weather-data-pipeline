import logging
import subprocess
import sys
import time
from pathlib import Path
import schedule

# Cấu hình log chuyên nghiệp
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [SCHEDULER] - %(message)s"
)

ROOT_DIR = Path(__file__).resolve().parent.parent
PYTHON_BIN = sys.executable  # Tự động lấy file thực thi python trong môi trường .venv


def job_run_pipeline():
    """Hàm kích hoạt chạy script run_incremental.py"""
    logging.info("⏰ Đến giờ hẹn! Đang khởi chạy Incremental Pipeline...")

    script_path = ROOT_DIR / "src" / "pipelines" / "run_incremental.py"
    if not script_path.exists():
        script_path = ROOT_DIR / "src" / "run_incremental.py"

    try:
        result = subprocess.run(
            [PYTHON_BIN, str(script_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        logging.info("✅ Pipeline đã hoàn thành thành công!")
        logging.info(f"Detail output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Lỗi khi chạy Pipeline: {e.stderr}")


def main():
    logging.info("🚀 Scheduler Daemon đã bắt đầu hoạt động...")

    # 1. Chạy ngay 1 lần đầu tiên khi Scheduler khởi động
    job_run_pipeline()

    # 2. Lập lịch tự động chạy lại hàng ngày lúc 06:00 sáng
    schedule.every().day.at("06:00").do(job_run_pipeline)

    logging.info("⏳ Đang lắng nghe lịch trình (Nhấn Ctrl + C để dừng Scheduler)...")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Thăm dò mỗi 60 giây


if __name__ == "__main__":
    main()
