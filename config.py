"""
CONFIGURATION SETTINGS - MULTI-URL ETHICAL MONITORING
Updated for Render deployment compatibility
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
    # URLs configuration - supports both local and Render
    MONITOR_URLS_ENV = os.environ.get('MONITOR_URLS', '').strip()
    if MONITOR_URLS_ENV:
        # Use URLs from environment variable on Render
        MONITOR_URLS = [url.strip() for url in MONITOR_URLS_ENV.split(',') if url.strip()]
    else:
        # Default URLs for local development
        MONITOR_URLS = [
            "https://tracking-system-10.onrender.com",
            "https://render-python-app-7i92.onrender.com"
        ]
    
    # Monitoring settings - ETHICAL intervals (minimum 5 minutes)
    CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', 300))  # 5 minutes in seconds - DO NOT MAKE THIS SMALLER
    TIMEOUT = int(os.environ.get('TIMEOUT', 10))
    USER_AGENT = os.environ.get('USER_AGENT', "EthicalMultiMonitor/1.0 (Termux)")
    
    # Storage settings
    JSON_DATA_PATH = DATA_DIR / "tracking_data.json"
    DATABASE_PATH = DATA_DIR / "tracking.db"
    LOG_FILE = LOGS_DIR / "monitor.log"
    
    # Automatic server settings detection
    # Detect if running on Render
    IS_RENDER = os.environ.get('RENDER') is not None
    
    # Automatically set host: 0.0.0.0 for Render, 127.0.0.1 for local
    HOST = "0.0.0.0" if IS_RENDER else "127.0.0.1"
    
    # Automatically detect port: use PORT from env on Render, default 5000 locally
    PORT = int(os.environ.get('PORT', 5000))
    
    # Debug mode: off on Render by default, configurable via env
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true' and not IS_RENDER
    
    # Rate limiting and storage
    STORAGE_LIMIT = int(os.environ.get('STORAGE_LIMIT', 1000))

config = Config()

# Print config info for debugging
if __name__ == '__main__':
    print("=" * 60)
    print("CONFIGURATION INFORMATION")
    print("=" * 60)
    print(f"Environment: {'Render' if config.IS_RENDER else 'Local'}")
    print(f"URLs to monitor: {len(config.MONITOR_URLS)}")
    for i, url in enumerate(config.MONITOR_URLS, 1):
        print(f"  {i}. {url}")
    print(f"Check interval: {config.CHECK_INTERVAL} seconds")
    print(f"Auto-detected Host: {config.HOST}")
    print(f"Auto-detected Port: {config.PORT}")
    print(f"Debug mode: {config.DEBUG} {'(auto-disabled on Render)' if config.IS_RENDER and os.environ.get('DEBUG', '').lower() == 'true' else ''}")
    print("=" * 60)
