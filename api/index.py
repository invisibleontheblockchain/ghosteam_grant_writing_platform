"""
Vercel Serverless Function Entry Point

Vercel's @vercel/python runtime auto-detects the `app` variable as a WSGI
application and serves it directly. No custom handler is needed.
"""

import os
import sys

# Add project root to Python path so `app.py` can resolve its local imports
# (engines/, services/, parsers/, config/, etc.)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask WSGI app — Vercel serves this automatically
from app import app