FROM python

RUN pip install pillow confluent-kafka

ADD manager.py ./

ENTRYPOINT python manager.py