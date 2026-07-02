"""
Vercel Serverless Function Entry Point

Re-exports the Flask `app` from app.py so Vercel can detect and serve it.
The top-level import gives Vercel a detectable Flask instance at this path.
"""

import os
import sys

# Add project root to Python path so `app.py` can resolve its local imports
# (engines/, services/, parsers/, config/, etc.)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask WSGI app — Vercel serves this automatically
from app import app  # noqa: F401 — re-exported for Vercel