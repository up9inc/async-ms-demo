import logging
import os
import time

from confluent_kafka import Consumer

TOPIC = "frontend-jobs"


def main():
    consumer = Consumer({
        'bootstrap.servers': os.environ.get("KAFKA", "localhost:9092"),
        'group.id': 'manager',
        'auto.offset.reset': 'earliest'  # earliest _committed_ offset
    })

    _wait_for_topic_to_exist(consumer, TOPIC)

    logging.info("Subscribing to topic: %s", TOPIC)
    consumer.subscribe([TOPIC])

    while True:
        logging.debug("Waiting for messages...")
        msg = consumer.poll()

        if msg is None:
            logging.warning("Poll timed out")
            break

        logging.info("Consuming message: %r %r", msg.key(), msg.value())

        if msg.error():
            logging.warning("Consumer error: {}".format(msg.error()))
            continue

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
