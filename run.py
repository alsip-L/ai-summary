# -*- coding: utf-8 -*-
"""Application entry point."""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from core.config_manager import ConfigManager

def main():
    """Main entry point."""
    # Read configuration from config.json
    settings = ConfigManager().get('system_settings', {})
    host = settings.get('host', '0.0.0.0')
    port = int(settings.get('port', 5000))
    debug = settings.get('debug', False)
    
    print(f"Starting AI Summary application...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Access: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    
    app.run(host=host, port=port, debug=debug, use_reloader=False)

if __name__ == '__main__':
    main()
