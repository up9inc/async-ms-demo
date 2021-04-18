FROM python

RUN pip install pillow confluent-kafka pika

ADD manager.py ./

ENTRYPOINT python manager.py