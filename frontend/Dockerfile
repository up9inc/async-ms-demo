FROM python
EXPOSE 5000

RUN pip install flask confluent-kafka

ADD frontend.py ./
ADD spa.html ./

ENTRYPOINT python frontend.py