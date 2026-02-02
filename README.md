# Ethical Website Monitor

A respectful website monitoring system that follows ethical guidelines and respects server resources.

## ⚠️ IMPORTANT DISCLAIMER

This software is **ONLY** for monitoring websites that:
- You own
- You have explicit permission to monitor
- Have APIs that allow monitoring

**DO NOT** use this tool to:
- Monitor websites without permission
- Send excessive requests (DDoS)
- Bypass rate limits
- Violate terms of service

## Features

- ✅ Ethical monitoring with proper intervals (5+ minutes)
- ✅ Dashboard with real-time status
- ✅ Data storage in JSON and SQLite
- ✅ Background scheduling
- ✅ Rate limiting
- ✅ Mobile-friendly interface

## Installation

### Termux (Android)

```bash
# Install Python
pkg install python

# Clone or create project
cd ~
mkdir ethical-monitor
cd ethical-monitor

# Copy all files to this directory
# ... (copy all the files created above)

# Make run script executable
chmod +x run.sh

# Install dependencies
pip install -r requirements.txt

# Run the application
./run.sh
