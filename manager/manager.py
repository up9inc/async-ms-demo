import io
import logging
import os
import time
from threading import Thread

from PIL import Image
from confluent_kafka import Consumer, Producer

producer = Producer({'bootstrap.servers': os.environ.get("KAFKA", "localhost:9092"), "message.send.max.retries": 2})

jobs_in_progress = {}


def assign_jobs(key, val):
    logging.info("Sending job into RedisMQ: %s", key)
    jobs_in_progress[key] = {"orig": val, "created": time.time()}
    producer.produce("grayscaler-job", key=key, value=val)


def fetch_results():
    run_consumer("grayscaler-result", callback)


def callback(msg):
    key = msg.key()
    if key not in jobs_in_progress:
        logging.warning("Key not found in active jobs: %s", key)
        return
    jobs_in_progress[key]["grayscale"] = msg.value()
    result_if_ready(key)


def result_if_ready(key):
    item = jobs_in_progress[key]
    if "grayscale" in item:
        img = Image.open(io.BytesIO(item['orig']))
        gray = Image.open(io.BytesIO(item['grayscale']))
        img.paste(gray.crop((gray.width // 2, 0, gray.width, gray.height)), (img.width // 2, 0))

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        logging.info("Result is ready, sending it into Kafka: %s", key)
        producer.produce("manager-results", key=key, value=img_byte_arr)


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


def main():
    def handler(msg):
        assign_jobs(msg.key(), msg.value())

    run_consumer("manager-jobs", handler)


def _wait_for_topic_to_exist(consumer, topic):
    while True:
        topics = consumer.list_topics(topic)  # promises to create topic
        logging.debug("Topic state: %s", topics.topics)
        if topics.topics[topic].error is None:
            break
        else:
            logging.warning("Topic is not available: %s", topics.topics[topic].error)
            time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO,
                        format='[%(asctime)s %(name)s %(levelname)s] %(message)s')

    Thread(target=fetch_results, daemon=True).start()
    main()
