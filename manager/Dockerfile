FROM python

RUN pip install confluent-kafka

ADD manager.py ./

ENTRYPOINT python manager.py