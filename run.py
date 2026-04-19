# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from core.config import ConfigManager


def main():
    settings = ConfigManager().get('system_settings', {})
    host = settings.get('host', '0.0.0.0')
    port = int(settings.get('port', 5000))
    debug = settings.get('debug', False)

    print(f"Starting AI Summary application...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Access: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
    )


if __name__ == '__main__':
    main()
