import requests
import socket
import ssl
from urllib.parse import urlparse

url = "https://www.gula-platform.org/"
parsed = urlparse(url)

print("--- HTTP Headers Audit ---")
try:
    resp = requests.head(url, timeout=10)
    for k, v in resp.headers.items():
        print(f"{k}: {v}")
except Exception as e:
    print(f"Error fetching headers: {e}")

print("\n--- SSL/TLS Certificate Audit ---")
try:
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = True
    with socket.create_connection((parsed.hostname, 443), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=parsed.hostname) as ssock:
            cert = ssock.getpeercert()
            print(f"Subject: {dict(x[0] for x in cert.get('subject', []))}")
            print(f"Issuer: {dict(x[0] for x in cert.get('issuer', []))}")
            print(f"Version: {cert.get('version')}")
            print(f"Not Before: {cert.get('notBefore')}")
            print(f"Not After: {cert.get('notAfter')}")
except Exception as e:
    print(f"Error inspecting SSL: {e}")
