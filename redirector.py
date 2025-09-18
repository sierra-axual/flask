# redirector.py
import os
import logging
from flask import Flask, request, redirect, Response
import requests

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/redirect')
def ssrf_redirect():
    target = request.args.get('target')
    app.logger.info("redirect hit from %s -> %s", request.remote_addr, target)
    if not target:
        return "Missing 'target' parameter", 400
    return redirect(target, code=302)

@app.route('/proxy')
def ssrf_proxy():
    target = request.args.get('target')
    app.logger.info("proxy hit from %s -> %s", request.remote_addr, target)
    if not target:
        return "Missing 'target' parameter", 400
    try:
        r = requests.get(target, headers={'Metadata': 'true'}, timeout=5)
        content_type = r.headers.get('Content-Type', 'text/plain')
        return Response(r.content, status=r.status_code, content_type=content_type)
    except Exception as e:
        app.logger.exception("proxy error for %s", target)
        return f"Error: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    # IMPORTANT: bind to 0.0.0.0 so Render can reach it
    app.run(host='0.0.0.0', port=port)
