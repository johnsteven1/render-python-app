"""
CONFIGURATION SETTINGS - MULTI-URL ETHICAL MONITORING
"""
import os
from pathlib import Path

class Config:
    # Base paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    TEMPLATES_DIR = BASE_DIR / "templates"
    STATIC_DIR = BASE_DIR / "static"
    
    # Create directories
    for directory in [DATA_DIR, LOGS_DIR, STATIC_DIR]:
        directory.mkdir(exist_ok=True)
    
    # ⚠️ IMPORTANT: Only monitor websites you own or have permission to monitor
    # Example URLs - CHANGE THESE to your own websites
    MONITOR_URLS = [
        "https://tracking-system-10.onrender.com",
        "https://render-python-app-7i92.onrender.com"
    ]
    
    # Monitoring settings - ETHICAL intervals (minimum 5 minutes)
    CHECK_INTERVAL = 100  # 5 minutes in seconds - DO NOT MAKE THIS SMALLER
    TIMEOUT = 10
    USER_AGENT = "EthicalMultiMonitor/1.0 (Termux)"
    
    # Storage settings
    JSON_DATA_PATH = DATA_DIR / "tracking_data.json"
    DATABASE_PATH = DATA_DIR / "tracking.db"
    LOG_FILE = LOGS_DIR / "monitor.log"
    
    # Server settings for Termux
    HOST = "127.0.0.1"
    PORT = 5000
    DEBUG = False
    
    # Rate limiting and storage
    STORAGE_LIMIT = 1000

config = Config()
