#!/usr/bin/env python3
"""Main entry point for the Password Manager application."""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Only enable debug mode if explicitly set in environment
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode)
