import requests

# Test file upload
url = 'http://localhost:5000/api/files/upload'

# Create a simple test file
test_content = "This is a test file for upload."
files = {'file': ('test.txt', test_content, 'text/plain')}
data = {
    'category': 'test',
    'grant_id': '1'
}

try:
    response = requests.post(url, files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
