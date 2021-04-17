import logging
import os
import time

from confluent_kafka import Producer
from flask import Flask, send_file

app = Flask(__name__)

producer = Producer({'bootstrap.servers': os.environ.get("KAFKA", "localhost:9092"), "message.send.max.retries": 2})


def produce(queue, key, val, headers=None):
    logging.info("Producing into %s: %s %s", queue, key, val)
    producer.poll(0)
    log_status = lambda x, y: logging.info("Done producing: %s %s", x, y)
    producer.produce(queue, key=key, value=val, headers=headers, on_delivery=log_status)
    producer.flush()


@app.route('/', methods=('get',))
def root():
    produce("frontend-jobs", "fe-%s" % time.time(), "myval-%s" % time.time())
    return send_file("spa.html")


@app.route('/', methods=('post',))
def post():
    return send_file("spa.html")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO,
                        format='[%(asctime)s %(name)s %(levelname)s] %(message)s')
    app.run(host='0.0.0.0')
