#!/usr/bin/env python3
"""
Backend startup script for Grant Writing Platform
Installs dependencies and starts the Flask server
"""

import os
import sys
import subprocess

def install_dependencies():
    """Install backend dependencies"""
    print("📦 Installing backend dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'backend_requirements.txt'])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def start_server():
    """Start the Flask server"""
    print("🚀 Starting Grant Writing Platform Backend...")
    print("🔗 API will be available at: http://localhost:5000")
    print("📊 Health check: http://localhost:5000/api/health")
    print("💡 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Run the Flask app
        subprocess.check_call([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")

def main():
    print("🏗️  Grant Writing Platform Backend Setup")
    print("=" * 50)
    
    # Check if dependencies need to be installed
    if not os.path.exists('grant_platform.db'):
        print("🗄️  First time setup detected")
        if not install_dependencies():
            return
    
    # Start the server
    start_server()

if __name__ == '__main__':
    main()
