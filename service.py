from flask import Flask, jsonify, Response, request
from prometheus_client import start_http_server, Counter, generate_latest, CONTENT_TYPE_LATEST, Gauge, REGISTRY
from datetime import datetime, timedelta
import requests
import subprocess

from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

REQUESTS_PER_IP = Gauge(
    'service_a_requests_per_ip',
    'Number of requests in the last 30 seconds per IP',
    ['ip']
)

request_counts = {}

metrics = PrometheusMetrics(app)

@app.route('/get_value', methods=['GET'])
def get_value():
    global request_counts
    client_ip = request.remote_addr
    current_time = datetime.now()

    request_counts = {
        ip: [t for t in times if t > current_time - timedelta(seconds=30)]
        for ip, times in request_counts.items()
    }

    if client_ip not in request_counts:
        request_counts[client_ip] = []
    request_counts[client_ip].append(current_time)

    return jsonify({"value": "This is a value from App 1"}), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    for ip, times in request_counts.items():
        REQUESTS_PER_IP.labels(ip=ip).set(len(times))
    return generate_latest(REGISTRY), 200

@app.route('/block_ip', methods=['POST'])
def block_ip():
    data = request.get_json()
    ip_address = data.get('ip')

    try:
        command = ["iptables", "-A", "INPUT", "-s", ip_address, "-j", "DROP"]
        subprocess.run(command, check=True)
        return {"message": f"Blocked Ip: {ip_address}"}, 200
    except subprocess.CalledProcessError as e:
        return {"message": f"Failed to block IP: {ip_address}"}, 500

def register_with_consul():
    payload = {
        "ID": "app1",
        "Name": "service_a",
        "Tags": ["flask"],
        "Address": "localhost",
        "Port": 5000,
        "Check": {
            "http": "http://10.151.101.11:5000/get_value",
            "Interval": "10s"
        }
    }
    requests.put("http://10.151.101.98:8500/v1/agent/service/register", json=payload)

if __name__ == '__main__':
    register_with_consul()
    app.run(debug=True, host='0.0.0.0', port=5000)