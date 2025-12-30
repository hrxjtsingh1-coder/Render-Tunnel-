# render_server.py - Updated for Cloudflare Tunnel
from flask import Flask, request, Response
import urllib3
import os
import json

app = Flask(__name__)

# ========== CONFIGURATION ==========
# Your permanent Cloudflare Tunnel URL
PHONE_TUNNEL_URL = "http://phone.coachsaab.online"  # Your tunnel URL

# YouTube target (for direct testing)
YT_SHORTS_URL = "https://youtube.com/shorts/XX8x7visJTQ?si=ZQt04Nft-JFslSEI"  # CHANGE THIS
# ===================================

# Create a session with connection pooling
http = urllib3.PoolManager(timeout=urllib3.Timeout(connect=5.0, read=15.0))

@app.route('/')
def home():
    """Simple home page to test if server is running."""
    return """
    <h1>Render Proxy Bridge</h1>
    <p>Status: <strong>Active</strong></p>
    <p>Tunnel URL: {}</p>
    <p>Test endpoints:</p>
    <ul>
        <li><a href="/status">/status</a> - Check server status</li>
        <li><a href="/test">/test</a> - Test tunnel connection</li>
        <li><a href="/view">/view</a> - Test YouTube view (via tunnel)</li>
    </ul>
    """.format(PHONE_TUNNEL_URL)

@app.route('/status')
def status():
    """Check if server and tunnel are running."""
    try:
        # Test if tunnel is responsive
        test_response = http.request('GET', PHONE_TUNNEL_URL, timeout=5.0)
        tunnel_status = test_response.status == 200
    except Exception:
        tunnel_status = False
    
    return {
        "status": "Render Bridge Active",
        "tunnel_url": PHONE_TUNNEL_URL,
        "tunnel_active": tunnel_status,
        "timestamp": os.popen('date').read().strip()
    }

@app.route('/test')
def test_tunnel():
    """Test the tunnel connection by fetching IP."""
    try:
        # Request through your phone tunnel
        response = http.request('GET', f'{PHONE_TUNNEL_URL}/httpbin.org/ip', timeout=10.0)
        
        if response.status == 200:
            data = json.loads(response.data.decode('utf-8'))
            return {
                "success": True,
                "message": "Tunnel is working!",
                "your_phone_ip": data.get('origin', 'Unknown'),
                "via": PHONE_TUNNEL_URL
            }
        else:
            return {"success": False, "error": f"Tunnel returned status {response.status}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/view')
def test_youtube_view():
    """Test a YouTube view through the tunnel."""
    try:
        # Construct the full YouTube URL
        yt_url = YT_SHORTS_URL
        
        # Make request through tunnel
        response = http.request('GET', f'{PHONE_TUNNEL_URL}/{yt_url}', timeout=20.0)
        
        # Check if we got a YouTube page
        html = response.data.decode('utf-8', errors='ignore')
        
        if "YouTube" in html or "youtube" in html:
            return {
                "success": True,
                "message": "YouTube page loaded successfully through tunnel!",
                "status_code": response.status,
                "content_length": len(html),
                "note": "Check YouTube Studio analytics in 15-30 minutes for the view."
            }
        else:
            return {
                "success": False,
                "message": "Loaded but doesn't look like YouTube",
                "status_code": response.status,
                "preview": html[:200] + "..."
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/proxy/<path:url>', methods=['GET'])
def proxy_to_phone(url):
    """Proxy endpoint for Colab bot."""
    try:
        # Ensure URL has protocol
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Forward request through Cloudflare Tunnel
        full_url = f'{PHONE_TUNNEL_URL}/{url}'
        
        # Forward headers (remove Host to avoid conflicts)
        headers = dict(request.headers)
        if 'Host' in headers:
            del headers['Host']
        
        # Make the request
        response = http.request(
            'GET',
            full_url,
            headers=headers,
            timeout=urllib3.Timeout(connect=10.0, read=30.0)
        )
        
        # Return the response
        return Response(
            response.data,
            status=response.status,
            headers=dict(response.headers)
        )
        
    except Exception as e:
        return f"Proxy Error: {str(e)}", 500

@app.route('/direct/<path:subpath>', methods=['GET'])
def direct_tunnel(subpath):
    """Direct access to any URL through tunnel."""
    try:
        target_url = f'{PHONE_TUNNEL_URL}/{subpath}'
        response = http.request('GET', target_url, timeout=15.0)
        return Response(response.data, status=response.status, headers=dict(response.headers))
    except Exception as e:
        return f"Direct access error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Server starting on port {port}")
    print(f"🔗 Tunnel URL: {PHONE_TUNNEL_URL}")
    print(f"🎯 YouTube target: {YT_SHORTS_URL}")
    print(f"📊 Status page: http://localhost:{port}/status")
    app.run(host='0.0.0.0', port=port)
