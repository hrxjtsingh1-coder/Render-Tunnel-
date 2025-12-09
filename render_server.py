# render_server.py - The public bridge on Render.com
from flask import Flask, request, Response
import urllib3
import os

app = Flask(__name__)

# Store the phone's ngrok tunnel URL (will be updated by phone)
PHONE_TUNNEL_URL = None

@app.route('/proxy/<path:url>', methods=['GET'])
def proxy_to_phone(url):
    """Main proxy endpoint. Colab bot calls this, we forward through phone's tunnel."""
    global PHONE_TUNNEL_URL

    if not PHONE_TUNNEL_URL:
        return "Error: Phone tunnel is not active. Is your Termux script running?", 503

    if not url.startswith('http'):
        url = 'https://' + url

    try:
        # Use the ngrok tunnel URL as a proxy
        http = urllib3.ProxyManager(PHONE_TUNNEL_URL)
        resp = http.request('GET', url, headers=request.headers, 
                          timeout=urllib3.Timeout(connect=10.0, read=30.0))
        return Response(resp.data, status=resp.status, headers=dict(resp.headers))
    except Exception as e:
        return f"Proxy Error via Phone Tunnel: {e}", 500

@app.route('/status')
def status():
    """Check if server is running."""
    return {"status": "Render Bridge Active", "phone_tunnel": PHONE_TUNNEL_URL is not None}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    print(f"[*] Server starting on port {port}")
    app.run(host='0.0.0.0', port=port)
