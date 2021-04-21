import io
import logging
import os
import time
from threading import Thread

from PIL import Image
from confluent_kafka import Producer, Consumer
from flask import Flask, send_file, jsonify, request, Response

app = Flask(__name__)

producer = Producer({'bootstrap.servers': os.environ.get("KAFKA", "localhost:9092"), "message.send.max.retries": 2})


def produce(queue, key, val, headers=None):
    logging.debug("Producing into %s: %s %s", queue, key, val)
    producer.poll(0)
    log_status = lambda x, y: logging.debug("Done producing: %s %s", x, y)
    producer.produce(queue, key=key, value=val, headers=headers, on_delivery=log_status)
    producer.flush()


def run_consumer(queue, msg_handler):
    consumer = Consumer({
        'bootstrap.servers': os.environ.get("KAFKA", "localhost:9092"),
        'group.id': 'manager',
        'auto.offset.reset': 'earliest'  # earliest _committed_ offset
    })

    _wait_for_topic_to_exist(consumer, queue)

    logging.info("Subscribing to topic: %s", queue)
    consumer.subscribe([queue])

    while True:
        logging.debug("Waiting for messages in %r...", queue)
        msg = consumer.poll()

        if msg is None:
            logging.warning("Poll timed out")
            break

        logging.info("Consuming Kafka message: %r", msg.key())

        if msg.error():
            logging.warning("Consumer error: {}".format(msg.error()))
            continue

        msg_handler(msg)

        consumer.commit()


def _wait_for_topic_to_exist(consumer, topic):
    while True:
        topics = consumer.list_topics(topic)  # promises to create topic
        logging.debug("Topic state: %s", topics.topics)
        if topics.topics[topic].error is None:
            break
        else:
            logging.warning("Topic is not available: %s", topics.topics[topic].error)
            time.sleep(1)


@app.route('/', methods=('get',))
def root():
    return send_file("spa.html")


@app.route('/', methods=('post',))
def post():
    image = Image.open(request.files['file'].stream).convert("RGB")

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    assert len(img_byte_arr) < 1024 * 1024, "Image size has to be smaller than 1MB"

    key = "fe-%s" % time.time()
    logging.info("Starting job: %s", key)
    produce("manager-jobs", key, img_byte_arr)
    return jsonify(key)


results = {}  # TODO: time-based purging


@app.route('/result', methods=('get',))
def result():
    result = results.get(request.args.get('key'))
    if result:
        return Response(result, mimetype='image/png')
    else:
        return Response(status=204)


def read_results():
    def handler(msg):
        results[msg.key().decode("ascii")] = msg.value()

    run_consumer("manager-results", handler)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO,
                        format='[%(asctime)s %(name)s %(levelname)s] %(message)s')
    Thread(target=read_results).start()

    app.run(host='0.0.0.0', debug=True)
