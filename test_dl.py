import urllib.request, json, time, uuid

boundary = uuid.uuid4().hex
with open('test_docs/pdfs/01_simple_article.pdf', 'rb') as f: data = f.read()
body = b'--' + boundary.encode() + b'\r\n'
body += b'Content-Disposition: form-data; name="file"; filename="01_simple_article.pdf"\r\n'
body += b'Content-Type: application/pdf\r\n\r\n' + data + b'\r\n'
body += b'--' + boundary.encode() + b'--\r\n'

req = urllib.request.Request('http://127.0.0.1:8000/api/upload', data=body, method='POST')
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
resp = urllib.request.urlopen(req)
job_id = json.loads(resp.read())['job_id']
time.sleep(3) # Wait for conversion

try:
    print('Testing markdown download for', job_id)
    resp2 = urllib.request.urlopen(f'http://127.0.0.1:8000/api/jobs/{job_id}/download/markdown')
    print('Markdown Headers:')
    print(resp2.headers)
except Exception as e:
    print('Markdown Error:', e)
    if hasattr(e, 'read'): print('Body:', e.read())
