import logging
import os
import time
from threading import Thread

import pika
from confluent_kafka import Consumer, Producer
from pika import BasicProperties
from pika.exceptions import AMQPConnectionError

TOPIC_JOBS_IN = "manager-jobs"
QUEUE_RMQ_OUT = "grayscaler-job"


def get_rmq_conn():
    while True:
        try:
            rmq_conn = pika.BlockingConnection(
                pika.ConnectionParameters(os.environ.get('RABBITMQ', 'localhost'), heartbeat=60))
            break
        except AMQPConnectionError:
            logging.warning("Failed to connect to RabbitMQ")
            time.sleep(1)
    return rmq_conn


producer = Producer({'bootstrap.servers': os.environ.get("KAFKA", "localhost:9092"), "message.send.max.retries": 2})

jobs_in_progress = {}


def assign_jobs(key, val, rmq_channel):
    logging.info("Sending job into RedisMQ: %s", key)

    jobs_in_progress[key] = {"orig": val, "created": time.time()}

    props = BasicProperties(headers={"key": key})
    rmq_channel.basic_publish(exchange='', routing_key=QUEUE_RMQ_OUT, body=val, properties=props)


def fetch_results():
    result_queue = "grayscaler-result"
    rmq_conn = get_rmq_conn()
    rmq_channel = rmq_conn.channel()
    rmq_channel.queue_declare(queue=result_queue)
    rmq_channel.basic_consume(queue=result_queue,
                              auto_ack=True,
                              on_message_callback=callback)
    logging.info("Waiting for input messages...")
    rmq_channel.start_consuming()


def result_if_ready(key):
    item = jobs_in_progress[key]
    if "grayscale" in item:
        final_result = item['orig'] + item['grayscale']  # TODO
        logging.info("Result is ready, sending it into Kafka: %s", key)
        producer.produce("manager-results", key, final_result)


def callback(ch, method, properties, body):
    logging.info("Received %r %r %r %r", ch, method, properties, body)
    key = properties.headers.get('key')
    jobs_in_progress[key]["grayscale"] = body
    result_if_ready(key)


def main():
    consumer = Consumer({
        'bootstrap.servers': os.environ.get("KAFKA", "localhost:9092"),
        'group.id': 'manager',
        'auto.offset.reset': 'earliest'  # earliest _committed_ offset
    })

    rmq_conn = get_rmq_conn()
    rmq_channel = rmq_conn.channel()
    rmq_channel.queue_declare(queue=QUEUE_RMQ_OUT)

    _wait_for_topic_to_exist(consumer, TOPIC_JOBS_IN)

    logging.info("Subscribing to topic: %s", TOPIC_JOBS_IN)
    consumer.subscribe([TOPIC_JOBS_IN])

    while True:
        logging.debug("Waiting for messages...")
        msg = consumer.poll()

        if msg is None:
            logging.warning("Poll timed out")
            break

        logging.info("Consuming Kafka message: %r", msg.key())

        if msg.error():
            logging.warning("Consumer error: {}".format(msg.error()))
            continue

        assign_jobs(msg.key(), msg.value(), rmq_channel)

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

    Thread(target=fetch_results, daemon=True).start()
    main()
