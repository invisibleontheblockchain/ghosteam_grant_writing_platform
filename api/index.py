"""
Vercel Serverless Function Entry Point

Vercel's @vercel/python runtime auto-detects the `app` variable as a WSGI
application and serves it directly. No custom handler is needed.
"""

import os
import sys
import traceback

# Add project root to Python path so `app.py` can resolve its local imports
# (engines/, services/, parsers/, config/, etc.)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask WSGI app — Vercel serves this automatically
try:
    from app import app
except Exception as e:
    # Log the full traceback so it appears in Vercel runtime logs
    traceback.print_exc()
    print(f"FATAL: Failed to import app: {e}", flush=True)

    # Provide a minimal WSGI app that returns the error so the function
    # doesn't silently die with no diagnostics
    from flask import Flask, jsonify
    app = Flask(__name__)

    error_message = str(e)
    tb = traceback.format_exc()

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def error_handler(path):
        return jsonify({
            "error": "Serverless function failed to initialize",
            "detail": error_message,
            "traceback": tb
        }), 500