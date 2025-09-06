import logging
import socket

from routes import app

logger = logging.getLogger(__name__)


@app.route('/', methods=['GET'])
def default_route():
    return 'Python Template'


logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# if __name__ == "__main__":
#     logging.info("Starting application ...")
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.bind(('localhost', 8080))
#     port = sock.getsockname()[1]
#     sock.close()
#     app.run(port=port)

if __name__ == "__main__":
    logging.info("Starting application ...")
    # Show all registered routes to verify /trivia is present
    for rule in app.url_map.iter_rules():
        methods = ",".join(sorted(m for m in rule.methods if m not in {"HEAD","OPTIONS"}))
        logging.info("Route: %-6s %s", methods, rule.rule)

    app.run(host="0.0.0.0", port=8080, debug=False)