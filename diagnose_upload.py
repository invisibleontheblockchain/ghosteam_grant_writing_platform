#!/usr/bin/env python3
"""
Upload Diagnostic Script - Identifies why frontend uploads might be failing
"""

print("🔍 UPLOAD DIAGNOSTIC REPORT")
print("=" * 50)

# 1. Check if backend is running
import requests
import json

try:
    health = requests.get('http://localhost:5000/api/health', timeout=5)
    print(f"✅ Backend Health: {health.status_code} - {health.json()['message']}")
except Exception as e:
    print(f"❌ Backend NOT responding: {e}")
    exit(1)

# 2. Test direct file upload
print("\n📁 Testing Direct File Upload...")
try:
    with open('README.md', 'rb') as f:
        files = {'file': ('README.md', f, 'text/markdown')}
        data = {'category': 'grant_documents', 'grant_id': '1'}
        
        response = requests.post('http://localhost:5000/api/files/upload', files=files, data=data)
        print(f"✅ Direct Upload: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   📄 File ID: {result['document_id']}")
            print(f"   📁 Filename: {result['filename']}")
        else:
            print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Direct Upload Failed: {e}")

# 3. Check proxy configuration
print("\n🔀 Checking Vite Proxy...")
try:
    with open('frontend/vite.config.js', 'r') as f:
        config = f.read()
        if 'proxy' in config and 'localhost:5000' in config:
            print("✅ Vite proxy configured correctly")
        else:
            print("❌ Vite proxy configuration issue")
except Exception as e:
    print(f"❌ Can't read Vite config: {e}")

# 4. Check if frontend is running on correct port
print("\n🌐 Checking Frontend Status...")
try:
    frontend = requests.get('http://localhost:3001', timeout=5)
    print(f"✅ Frontend responding on port 3001")
except Exception as e:
    print(f"❌ Frontend not responding on port 3001: {e}")

# 5. Test proxy route
print("\n🔀 Testing Proxy Route...")
try:
    proxy_health = requests.get('http://localhost:3001/api/health', timeout=5)
    print(f"✅ Proxy route working: {proxy_health.status_code}")
except Exception as e:
    print(f"❌ Proxy route failing: {e}")

# 6. Common frontend issues
print("\n🔧 COMMON FRONTEND UPLOAD ISSUES:")
print("=" * 50)

issues = [
    "🔸 CORS Issues: Browser blocking cross-origin requests",
    "🔸 File Size: File too large (>50MB backend limit)",
    "🔸 File Type: File extension not in allowed list (.txt, .pdf, .doc, .docx, .md, etc.)",
    "🔸 FormData Construction: Frontend not properly building FormData object",
    "🔸 Headers: Setting Content-Type manually instead of letting browser handle it",
    "🔸 Vite Proxy: Proxy not handling multipart/form-data correctly",
    "🔸 Network: Request timing out during large file upload",
    "🔸 Response Handling: Frontend not properly reading response",
    "🔸 Database: Error saving file metadata after successful upload",
    "🔸 Permissions: File system permissions preventing file write"
]

for issue in issues:
    print(issue)

print("\n💡 RECOMMENDED SOLUTIONS:")
print("=" * 50)
print("1. Check browser dev tools Network tab for exact error")
print("2. Verify file size < 50MB and allowed extension")
print("3. Ensure FormData doesn't set Content-Type header manually")
print("4. Test direct backend upload (bypass proxy)")
print("5. Check if grant_id exists in database")
print("6. Verify uploads directory permissions")

print("\n🏁 Diagnostic Complete!")
