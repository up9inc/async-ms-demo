import logging
import os
import time

from PIL import Image
from confluent_kafka import Producer
from flask import Flask, send_file, jsonify, request

app = Flask(__name__)

producer = Producer({'bootstrap.servers': os.environ.get("KAFKA", "localhost:9092"), "message.send.max.retries": 2})


def produce(queue, key, val, headers=None):
    logging.debug("Producing into %s: %s %s", queue, key, val)
    producer.poll(0)
    log_status = lambda x, y: logging.debug("Done producing: %s %s", x, y)
    producer.produce(queue, key=key, value=val, headers=headers, on_delivery=log_status)
    producer.flush()


@app.route('/', methods=('get',))
def root():
    return send_file("spa.html")


@app.route('/', methods=('post',))
def post():
    image = Image.open(request.files['file'].stream).convert("RGB")

    key = "fe-%s" % time.time()
    logging.info("Starting job: %s", key)
    produce("manager-jobs", key, "myval-%s" % time.time())
    return jsonify(key)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO,
                        format='[%(asctime)s %(name)s %(levelname)s] %(message)s')
    app.run(host='0.0.0.0')
