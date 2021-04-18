import logging
import os
import time

import pika
from confluent_kafka import Consumer
from pika.exceptions import AMQPConnectionError

TOPIC_JOBS_IN = "frontend-jobs"
QUEUE_RMQ_OUT = "grayscaler-job"

while True:
    try:
        rmq_conn = pika.BlockingConnection(
            pika.ConnectionParameters(os.environ.get('RABBITMQ', 'localhost'), heartbeat=60))
        break
    except AMQPConnectionError:
        logging.warning("Failed to connect to RabbitMQ")
        time.sleep(1)

rmq_channel = rmq_conn.channel()
rmq_channel.queue_declare(queue=QUEUE_RMQ_OUT)
jobs_in_progress = {}


def _process_job(key, val):
    logging.info("Sending job into RedisMQ: %s", key)
    rmq_channel.basic_publish(exchange='', routing_key=QUEUE_RMQ_OUT, body=val)


def main():
    consumer = Consumer({
        'bootstrap.servers': os.environ.get("KAFKA", "localhost:9092"),
        'group.id': 'manager',
        'auto.offset.reset': 'earliest'  # earliest _committed_ offset
    })

    _wait_for_topic_to_exist(consumer, TOPIC_JOBS_IN)

    logging.info("Subscribing to topic: %s", TOPIC_JOBS_IN)
    consumer.subscribe([TOPIC_JOBS_IN])

    while True:
        logging.debug("Waiting for messages...")
        msg = consumer.poll()

        if msg is None:
            logging.warning("Poll timed out")
            break

        logging.info("Consuming message: %r", msg)

        if msg.error():
            logging.warning("Consumer error: {}".format(msg.error()))
            continue

        _process_job(msg.key(), msg.value())

        consumer.commit()

    logging.info("Closing consumer")
    consumer.close()


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

    main()
    rmq_conn.close()
