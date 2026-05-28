import os
import sys
import requests
from flask import Flask, render_template, jsonify, request, Response

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))
from config import FOG_STATUS_URL, CLOUD_ANALYTICS_URL, REQUEST_TIMEOUT, FOG_HOST, FOG_PORT

app = Flask(__name__)

FOG_SNAPSHOT_BASE = f"http://{FOG_HOST}:{FOG_PORT}/snapshot"

# ── Views ─────────────────────────────────────────────

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/analytics")
def analytics_view():
    return render_template("analytics.html")

# ── Data endpoints ────────────────────────────────────

@app.route("/dashboard_data")
def dashboard_data():
    fog_data   = {}
    cloud_data = {}

    try:
        r = requests.get(FOG_STATUS_URL, timeout=REQUEST_TIMEOUT)
        fog_data = r.json()
        fog_data["fog_status"] = "ONLINE"
    except requests.exceptions.ConnectionError:
        fog_data = {"fog_status": "OFFLINE"}
    except requests.exceptions.Timeout:
        fog_data = {"fog_status": "TIMEOUT"}

    try:
        r = requests.get(CLOUD_ANALYTICS_URL, timeout=REQUEST_TIMEOUT)
        cloud_data = r.json()
        cloud_data["cloud_status"] = "ONLINE"
    except requests.exceptions.ConnectionError:
        cloud_data = {"cloud_status": "OFFLINE"}
    except requests.exceptions.Timeout:
        cloud_data = {"cloud_status": "TIMEOUT"}

    return jsonify({"fog": fog_data, "cloud": cloud_data})


@app.route("/analytics_data")
def analytics_data():
    date_filter = request.args.get("date", "")
    url = CLOUD_ANALYTICS_URL
    if date_filter:
        url += f"?date={date_filter}"

    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        data = r.json()
        data["cloud_status"] = "ONLINE"
        return jsonify(data)
    except requests.exceptions.ConnectionError:
        return jsonify({"cloud_status": "OFFLINE"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"cloud_status": "TIMEOUT"}), 504


@app.route("/proxy_snapshot/<filename>")
def proxy_snapshot(filename):
    """Proxy snapshot images from the fog server."""
    try:
        r = requests.get(
            f"{FOG_SNAPSHOT_BASE}/{filename}",
            timeout=REQUEST_TIMEOUT,
            stream=True,
        )
        return Response(r.content, content_type=r.headers.get("Content-Type", "image/jpeg"))
    except Exception:
        return "", 404


if __name__ == "__main__":
    app.run(debug=True, port=5003)