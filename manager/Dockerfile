FROM python

RUN pip install confluent-kafka pika

ADD manager.py ./

ENTRYPOINT python manager.py