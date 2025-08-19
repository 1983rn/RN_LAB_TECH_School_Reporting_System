#!/usr/bin/env python3
"""
WSGI Configuration for Malawi School Reporting System
Production deployment entry point
"""

import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Ensure template and static directories exist
os.makedirs(os.path.join(current_dir, 'templates'), exist_ok=True)
os.makedirs(os.path.join(current_dir, 'static'), exist_ok=True)

from app import app

# Create application instance for WSGI server
application = app

if __name__ == "__main__":
    application.run()