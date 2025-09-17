from flask import Flask, request, Response
import requests

app = Flask(__name__)

@app.route('/proxy')
def proxy():
    target = request.args.get('target')
    if not target:
        return "Missing 'target' param", 400

    try:
        r = requests.get(
            target,
            headers={'Metadata': 'true'},
            timeout=2
        )
        return Response(r.content, status=r.status_code)
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(port=8080)
