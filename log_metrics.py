import requests
import logging
import time
import json

PROMETHEUS_URL = "http://localhost:9090/api/v1/query"
METRIC_NAME = "service_a_requests_per_ip"
LOG_FILE = "/var/log/service_check.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(message)s'
)

def fetch_metric():
    query = {'query': METRIC_NAME}

    try:
        response = requests.get(PROMETHEUS_URL, params=query)
        response.raise_for_status()

        results = response.json()['data']['result']

        for result in results:
            ip = result['metric']['ip']
            request_count = float(result['value'][1])
            if request_count >= 10:
                log_message = f"DoS attack from: {ip} with {int(request_count)} requests"
                logging.warning(log_message)
                print(f"DoS attack from: {ip} with {int(request_count)} requests")

    except Exception as e:
        logging.error(json.dumps({
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            "metric": METRIC_NAME,
            "error": str(e)
        }))

if __name__ == "__main__":
    while True:
        fetch_metric()
        time.sleep(15)