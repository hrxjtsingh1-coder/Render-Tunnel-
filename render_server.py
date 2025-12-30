# render_server.py - CORRECTED FOR CLOUDFLARE TUNNEL
from flask import Flask, request, Response
import urllib3
import os
import json
from urllib.parse import urljoin

app = Flask(__name__)

# ========== CONFIGURATION ==========
# Your Cloudflare Tunnel URL (NO trailing slash for urljoin to work correctly)
PHONE_TUNNEL_BASE_URL = "http://phone.coachsaab.online"

# Test YouTube Shorts URL (CHANGE THIS to your actual test video)
TEST_YT_SHORTS_URL = "https://www.youtube.com/shorts/VIDEO_ID_HERE"
# ===================================

# Create HTTP connection pool
http = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=5.0, read=15.0),
    retries=urllib3.Retry(3, redirect=2)
)

def make_tunnel_request(url_path):
    """Make a request through the Cloudflare Tunnel."""
    # Construct full URL
    full_url = urljoin(PHONE_TUNNEL_BASE_URL + '/', url_path.lstrip('/'))
    
    try:
        response = http.request(
            'GET',
            full_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return response
    except Exception as e:
        raise Exception(f"Tunnel request failed: {str(e)}")

@app.route('/')
def home():
    return """
    <h1>📡 Render Proxy Bridge - ACTIVE</h1>
    <p>Tunnel URL: <code>{}</code></p>
    <p>Test endpoints:</p>
    <ul>
        <li><a href="/status">/status</a> - Server & tunnel status</li>
        <li><a href="/test/ip">/test/ip</a> - Show your phone's IP</li>
        <li><a href="/test/yt">/test/yt</a> - Test YouTube connection</li>
        <li><a href="/proxy/https://httpbin.org/ip">/proxy/https://httpbin.org/ip</a> - Proxy test</li>
    </ul>
    """.format(PHONE_TUNNEL_BASE_URL)

@app.route('/status')
def status():
    """Check server and tunnel status."""
    tunnel_active = False
    try:
        # Quick ping to tunnel
        resp = http.request('GET', PHONE_TUNNEL_BASE_URL, timeout=3.0)
        tunnel_active = resp.status in [200, 404, 502]  # Any response means tunnel is reachable
    except:
        pass
    
    return {
        "server": "active",
        "timestamp": os.popen('date').read().strip(),
        "tunnel": {
            "url": PHONE_TUNNEL_BASE_URL,
            "active": tunnel_active,
            "note": "true means tunnel is reachable (may return error page)"
        }
    }

@app.route('/test/ip')
def test_ip():
    """Test tunnel by getting phone's IP address."""
    try:
        response = make_tunnel_request('httpbin.org/ip')
        if response.status == 200:
            data = json.loads(response.data.decode('utf-8'))
            return {
                "success": True,
                "message": "✅ Tunnel is working!",
                "your_phone_ip": data.get('origin', 'Unknown'),
                "via_tunnel": PHONE_TUNNEL_BASE_URL
            }
        return {"success": False, "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/test/yt')
def test_youtube():
    """Test YouTube connection through tunnel."""
    try:
        response = make_tunnel_request(TEST_YT_SHORTS_URL)
        html = response.data.decode('utf-8', errors='ignore')[:500]  # First 500 chars
        
        is_youtube = 'youtube' in html.lower() or 'YouTube' in html
        
        return {
            "success": True,
            "youtube_detected": is_youtube,
            "status_code": response.status,
            "preview": html,
            "note": "If youtube_detected is true, tunnel can access YouTube"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/proxy/<path:target_url>')
def proxy_request(target_url):
    """Main proxy endpoint for Colab bot."""
    try:
        # Ensure URL has protocol
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url
        
        # Forward request through tunnel
        response = make_tunnel_request(target_url)
        
        # Return response to client
        return Response(
            response.data,
            status=response.status,
            headers=dict(response.headers)
        )
        
    except Exception as e:
        return Response(
            json.dumps({"error": "Proxy failed", "details": str(e)}),
            status=500,
            mimetype='application/json'
        )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Server starting on port {port}")
    print(f"🔗 Cloudflare Tunnel: {PHONE_TUNNEL_BASE_URL}")
    print(f"📺 Test YouTube: {TEST_YT_SHORTS_URL}")
    app.run(host='0.0.0.0', port=port)
