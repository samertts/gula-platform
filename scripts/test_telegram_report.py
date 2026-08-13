import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append('/home/ubuntu/gula-platform/backend')

from app.services.telegram_bot_commands import handle_telegram_command
from app.database import Base

# Setup local test DB if needed, or use existing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gula_test.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def generate_report():
    db = SessionLocal()
    try:
        print("--- GULA Telegram Bot Test Report ---")

        print("\n[Command: /status]")
        status_report = handle_telegram_command("/status", "test_chat", db)
        print(status_report)

        print("\n[Command: /alerts]")
        alerts_report = handle_telegram_command("/alerts", "test_chat", db)
        print(alerts_report)

        print("\n[Command: /stats]")
        stats_report = handle_telegram_command("/stats", "test_chat", db)
        print(stats_report)

        print("\n-------------------------------------")
    finally:
        db.close()

if __name__ == "__main__":
    generate_report()
