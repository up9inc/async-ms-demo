FROM python

RUN pip install confluent-kafka pillow

ADD grayscale.py ./

ENTRYPOINT python grayscale.py