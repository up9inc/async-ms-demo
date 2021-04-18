import logging
import os
import time

from confluent_kafka import Consumer, Producer

producer = Producer({'bootstrap.servers': os.environ.get("KAFKA", "localhost:9092"), "message.send.max.retries": 2})


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


def callback(msg):
    key = msg.key()
    body = msg.value()
    body = body.decode('ascii')[::-1].encode('ascii')

    logging.info("Sending result back into RabbitMQ: %s", key)
    producer.produce("grayscaler-result", key=key, value=body)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO,
                        format='[%(asctime)s %(name)s %(levelname)s] %(message)s')

    run_consumer("grayscaler-job", callback)
