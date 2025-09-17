from flask import Flask, request, redirect

app = Flask(__name__)

@app.route('/redirect')
def ssrf_redirect():
    target = request.args.get('target')
    if not target:
        return "Missing 'target' parameter", 400
    return redirect(target, code=302)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
