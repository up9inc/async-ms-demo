import logging
import os
import time

import pika
from pika import BasicProperties
from pika.exceptions import AMQPConnectionError

QUEUE_RMQ_IN = "grayscaler-job"
QUEUE_RMQ_OUT = "grayscaler-result"

while True:
    try:
        rmq_conn = pika.BlockingConnection(
            pika.ConnectionParameters(os.environ.get('RABBITMQ', 'localhost'), heartbeat=60))
        break
    except AMQPConnectionError:
        logging.warning("Failed to connect to RabbitMQ")
        time.sleep(1)

rmq_channel = rmq_conn.channel()
rmq_channel.queue_declare(queue=QUEUE_RMQ_IN)


def main():
    rmq_channel.basic_consume(queue=QUEUE_RMQ_IN,
                              auto_ack=True,
                              on_message_callback=callback)
    logging.info("Waiting for input messages...")
    rmq_channel.start_consuming()


def callback(ch, method, properties, body):
    logging.info("Received %r %r %r %r", ch, method, properties, body)
    key = properties.headers.get('key')

    body = body.decode('ascii')[::-1].encode('ascii')

    logging.info("Sending result back into RabbitMQ: %s", key)
    props = BasicProperties(headers={"key": key})
    rmq_channel.basic_publish(exchange='', routing_key=QUEUE_RMQ_OUT, body=body, properties=props)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO,
                        format='[%(asctime)s %(name)s %(levelname)s] %(message)s')

    main()
