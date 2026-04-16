# -*- coding: utf-8 -*-
"""Application entry point."""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

def main():
    """Main entry point."""
    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting AI Summary application...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Access: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    
    app.run(host=host, port=port, debug=debug, use_reloader=False)

if __name__ == '__main__':
    main()
