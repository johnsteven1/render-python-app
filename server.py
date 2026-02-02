"""
ETHICAL MULTI-URL MONITORING SERVER
Monitors multiple websites with proper intervals
Optimized for Render deployment
"""
from flask import Flask, render_template, jsonify, request
import requests
import json
import time
from datetime import datetime
from pathlib import Path
import sqlite3
import logging
import os
import threading
import sys

from config import config

app = Flask(__name__)

# Setup logging - enhanced for Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)  # Use sys.stdout for Render
    ]
)
logger = logging.getLogger(__name__)

# Set timezone
os.environ['TZ'] = 'UTC'
try:
    time.tzset()
except AttributeError:
    pass  # Windows compatibility

# Global variables
last_check_times = {url: 0 for url in config.MONITOR_URLS}
check_counts = {url: 0 for url in config.MONITOR_URLS}
monitoring_active = True

# Initialize data storage - Render compatibility
def init_database():
    """Initialize SQLite database"""
    try:
        # Use check_same_thread=False for SQLite in multi-threaded environments
        conn = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS website_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                url TEXT,
                status_code INTEGER,
                response_time REAL,
                success BOOLEAN,
                error_message TEXT
            )
        ''')
        
        # Add index for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url ON website_checks(url)')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {config.DATABASE_PATH}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        # Try alternative path for Render
        try:
            db_path = os.path.join(os.path.dirname(__file__), config.DATABASE_PATH)
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.close()
            logger.info(f"Database accessible at {db_path}")
        except Exception as e2:
            logger.error(f"Database still inaccessible: {e2}")

# Load existing JSON data
def load_tracking_data():
    """Load existing tracking data from JSON"""
    try:
        if config.JSON_DATA_PATH.exists():
            with open(config.JSON_DATA_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading tracking data: {e}")
    
    return {"checks": [], "statistics": {}}

# Save data to JSON
def save_tracking_data(data):
    """Save tracking data to JSON file"""
    try:
        with open(config.JSON_DATA_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving tracking data: {e}")

# Website checking function for single URL
def check_single_url(url):
    """Check a single website URL"""
    try:
        start_time = time.time()
        
        headers = {
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = requests.get(
            url,
            headers=headers,
            timeout=config.TIMEOUT
        )
        
        end_time = time.time()
        response_time = round(end_time - start_time, 3)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "status_code": response.status_code,
            "response_time": response_time,
            "success": response.status_code == 200,
            "error": None
        }
        
        return result, None
        
    except requests.exceptions.Timeout:
        error_msg = "Request timeout"
    except requests.exceptions.ConnectionError:
        error_msg = "Connection error"
    except Exception as e:
        error_msg = str(e)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "status_code": 0,
        "response_time": 0,
        "success": False,
        "error": error_msg
    }
    
    return result, error_msg

# Ethical monitoring of all URLs
def ethical_multi_url_check():
    """Check all URLs with proper rate limiting"""
    global last_check_times, check_counts
    
    current_time = time.time()
    all_results = []
    
    for url in config.MONITOR_URLS:
        # Rate limiting - minimum 5 minutes between checks per URL
        if current_time - last_check_times[url] < config.CHECK_INTERVAL:
            continue
        
        last_check_times[url] = current_time
        check_counts[url] += 1
        
        logger.info(f"Checking {url} (Check #{check_counts[url]})")
        
        result, error = check_single_url(url)
        all_results.append(result)
        
        if error:
            logger.error(f"Check failed for {url}: {error}")
        else:
            logger.info(f"Check successful for {url}: Status {result['status_code']}")
        
        # Save each result
        save_to_database(result)
        
        # Small delay between checking different URLs (optional, for ethics)
        time.sleep(1)
    
    if all_results:
        # Save to JSON
        data = load_tracking_data()
        for result in all_results:
            data["checks"].append(result)
        
        # Limit stored entries
        if len(data["checks"]) > config.STORAGE_LIMIT:
            data["checks"] = data["checks"][-config.STORAGE_LIMIT:]
        
        # Update statistics
        update_statistics(data)
        save_tracking_data(data)
    
    return all_results

def update_statistics(data):
    """Update statistics for all URLs"""
    checks = data.get("checks", [])
    
    if not checks:
        data["statistics"] = {}
        return
    
    # Calculate statistics per URL
    stats = {}
    for url in config.MONITOR_URLS:
        url_checks = [c for c in checks if c.get("url") == url]
        
        if url_checks:
            successful = sum(1 for c in url_checks if c.get("success"))
            total = len(url_checks)
            
            stats[url] = {
                "total_checks": total,
                "successful_checks": successful,
                "uptime_percentage": round((successful / total * 100), 2) if total > 0 else 0,
                "last_check": url_checks[-1]["timestamp"] if url_checks else None
            }
    
    data["statistics"] = stats

def save_to_database(result):
    """Save result to SQLite database"""
    try:
        # Use check_same_thread=False for SQLite in multi-threaded environments
        conn = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO website_checks 
            (timestamp, url, status_code, response_time, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            result["timestamp"],
            result["url"],
            result["status_code"],
            result["response_time"],
            result["success"],
            result.get("error")
        ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to save to database: {e}")

# Background monitoring thread
def background_monitor():
    """Background monitoring thread for all URLs"""
    logger.info(f"Background monitoring started for {len(config.MONITOR_URLS)} URLs")
    logger.info(f"Interval: {config.CHECK_INTERVAL} seconds per URL")
    
    while monitoring_active:
        results = ethical_multi_url_check()
        
        if results:
            logger.info(f"Completed checks: {len(results)} URLs")
        else:
            logger.info("All URLs are rate limited, waiting...")
        
        # Wait for next check cycle
        time.sleep(config.CHECK_INTERVAL)
    
    logger.info("Background monitoring stopped")

# Flask Routes
@app.route('/')
def index():
    """Main dashboard page"""
    data = load_tracking_data()
    
    # Prepare dashboard data
    dashboard_data = {
        "urls": config.MONITOR_URLS,
        "statistics": data.get("statistics", {}),
        "recent_checks": data.get("checks", [])[-10:][::-1],  # Last 10, newest first
        "monitoring_info": {
            "interval": config.CHECK_INTERVAL,
            "active_urls": len(config.MONITOR_URLS),
            "monitoring_active": monitoring_active
        }
    }
    
    return render_template('index.html', data=dashboard_data)

@app.route('/api/status')
def get_status():
    """API endpoint for current status"""
    data = load_tracking_data()
    
    # Calculate next check times
    next_checks = {}
    current_time = time.time()
    
    for url in config.MONITOR_URLS:
        time_since_last = current_time - last_check_times[url]
        next_in = max(0, config.CHECK_INTERVAL - time_since_last)
        next_checks[url] = next_in
    
    response_data = {
        "checks": data.get("checks", []),
        "statistics": data.get("statistics", {}),
        "monitoring_info": {
            "urls": config.MONITOR_URLS,
            "interval": config.CHECK_INTERVAL,
            "next_checks": next_checks,
            "check_counts": check_counts,
            "monitoring_active": monitoring_active,
            "total_checks": sum(check_counts.values())
        }
    }
    
    return jsonify(response_data)

@app.route('/api/check-now', methods=['POST', 'GET'])
def check_now():
    """Manually trigger checks for all URLs"""
    global last_check_times
    
    current_time = time.time()
    
    # Check if any URL can be checked (not rate limited)
    can_check = False
    for url in config.MONITOR_URLS:
        if current_time - last_check_times[url] >= 30:  # 30 seconds minimum
            can_check = True
            break
    
    if not can_check:
        return jsonify({
            "error": "All URLs are rate limited. Please wait 30 seconds between checks.",
            "next_check_in": 30
        }), 429
    
    results = ethical_multi_url_check()
    
    if results:
        return jsonify({
            "message": f"Checks completed for {len(results)} URLs",
            "results": results,
            "next_check_available_in": 30
        })
    else:
        return jsonify({
            "message": "All checks skipped - rate limited",
            "next_check_in": config.CHECK_INTERVAL
        })

@app.route('/api/check-url/<int:url_index>', methods=['POST'])
def check_specific_url(url_index):
    """Check a specific URL by index"""
    if url_index < 0 or url_index >= len(config.MONITOR_URLS):
        return jsonify({"error": "Invalid URL index"}), 400
    
    url = config.MONITOR_URLS[url_index]
    current_time = time.time()
    
    # Rate limiting
    if current_time - last_check_times[url] < 30:
        return jsonify({
            "error": f"Please wait 30 seconds between checks for {url}",
            "wait_time": 30 - (current_time - last_check_times[url])
        }), 429
    
    result, error = check_single_url(url)
    
    if error:
        return jsonify({
            "message": f"Check failed for {url}",
            "error": error,
            "result": result
        }), 500
    else:
        # Save the result
        last_check_times[url] = current_time
        check_counts[url] += 1
        save_to_database(result)
        
        # Update JSON
        data = load_tracking_data()
        data["checks"].append(result)
        update_statistics(data)
        save_tracking_data(data)
        
        return jsonify({
            "message": f"Check completed for {url}",
            "result": result,
            "next_check_available_in": 30
        })

@app.route('/api/history')
def get_history():
    """Get check history with filtering options"""
    url_filter = request.args.get('url', 'all')
    limit = int(request.args.get('limit', 50))
    
    try:
        # Use check_same_thread=False for SQLite in multi-threaded environments
        conn = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
        cursor = conn.cursor()
        
        if url_filter != 'all' and url_filter in config.MONITOR_URLS:
            cursor.execute('''
                SELECT timestamp, url, status_code, response_time, success 
                FROM website_checks 
                WHERE url = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (url_filter, limit))
        else:
            cursor.execute('''
                SELECT timestamp, url, status_code, response_time, success 
                FROM website_checks 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = [
            {
                "timestamp": row[0],
                "url": row[1],
                "status_code": row[2],
                "response_time": row[3],
                "success": bool(row[4])
            }
            for row in rows
        ]
        
        return jsonify(history)
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        # Fallback to JSON
        data = load_tracking_data()
        checks = data.get("checks", [])
        
        if url_filter != 'all':
            checks = [c for c in checks if c.get("url") == url_filter]
        
        recent_checks = checks[-limit:] if len(checks) > limit else checks
        recent_checks.reverse()
        
        return jsonify(recent_checks)

@app.route('/api/control', methods=['POST'])
def control_monitoring():
    """Control monitoring (start/stop)"""
    global monitoring_active
    
    action = request.json.get('action')
    
    if action == 'stop':
        monitoring_active = False
        return jsonify({"message": "Monitoring stopped", "active": False})
    elif action == 'start':
        monitoring_active = True
        # Start monitoring thread if not already running
        if not hasattr(app, 'monitor_thread') or not app.monitor_thread.is_alive():
            app.monitor_thread = threading.Thread(target=background_monitor, daemon=True)
            app.monitor_thread.start()
        return jsonify({"message": "Monitoring started", "active": True})
    else:
        return jsonify({"error": "Invalid action. Use 'start' or 'stop'"}), 400

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "monitoring_active": monitoring_active,
        "urls_configured": len(config.MONITOR_URLS),
        "total_checks": sum(check_counts.values()),
        "environment": "Render" if config.IS_RENDER else "Local",
        "host": config.HOST,
        "port": config.PORT
    })

@app.route('/api/debug')
def debug_info():
    """Debug endpoint for troubleshooting"""
    return jsonify({
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "files_in_dir": os.listdir('.'),
        "database_exists": os.path.exists(config.DATABASE_PATH),
        "log_file_exists": os.path.exists(config.LOG_FILE),
        "json_data_exists": os.path.exists(config.JSON_DATA_PATH),
        "config_info": {
            "is_render": config.IS_RENDER,
            "host": config.HOST,
            "port": config.PORT,
            "debug": config.DEBUG,
            "monitor_urls_count": len(config.MONITOR_URLS),
            "check_interval": config.CHECK_INTERVAL
        }
    })

# Initialize application
def initialize_app():
    """Initialize the application for both local and Render"""
    # Initialize database
    init_database()
    
    # Perform initial checks
    logger.info(f"Performing initial checks for {len(config.MONITOR_URLS)} URLs...")
    initial_results = ethical_multi_url_check()
    
    if initial_results:
        logger.info(f"Initial checks completed: {len(initial_results)} URLs checked")
    else:
        logger.info("Initial checks completed")
    
    # Start background monitoring thread
    try:
        app.monitor_thread = threading.Thread(target=background_monitor, daemon=True)
        app.monitor_thread.start()
        logger.info("Background monitoring thread started")
    except Exception as e:
        logger.error(f"Failed to start monitoring thread: {e}")

# Entry point for Gunicorn
if __name__ == '__main__':
    initialize_app()
    
    # Display startup info
    logger.info(f"╔══════════════════════════════════════════════╗")
    logger.info(f"║     ETHICAL MULTI-URL MONITOR                ║")
    logger.info(f"╠══════════════════════════════════════════════╣")
    logger.info(f"║ Environment: {'Render' if config.IS_RENDER else 'Local'}")
    logger.info(f"║ URLs configured: {len(config.MONITOR_URLS)}")
    for i, url in enumerate(config.MONITOR_URLS):
        logger.info(f"║ {i+1}. {url}")
    logger.info(f"║ Interval: {config.CHECK_INTERVAL}s ({config.CHECK_INTERVAL//60}min)")
    logger.info(f"║ Host: {config.HOST}")
    logger.info(f"║ Port: {config.PORT}")
    logger.info(f"║ Debug mode: {config.DEBUG}")
    logger.info(f"║ Health check: /health")
    logger.info(f"║ Debug info: /api/debug")
    logger.info(f"╚══════════════════════════════════════════════╝")
    
    logger.info("⚠️  REMINDER: Only monitor websites you own or have permission to monitor")
    
    try:
        # Use the automatically detected host and port from config
        app.run(
            host=config.HOST,  # Automatically 0.0.0.0 on Render, 127.0.0.1 locally
            port=config.PORT,  # Automatically detected from environment or default
            debug=config.DEBUG,  # Automatically disabled on Render
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        monitoring_active = False
        if hasattr(app, 'monitor_thread') and app.monitor_thread.is_alive():
            app.monitor_thread.join(timeout=5)
    except Exception as e:
        logger.error(f"Server error: {e}")
