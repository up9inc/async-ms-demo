FROM java

EXPOSE 9092

WORKDIR /tmp

RUN wget https://downloads.apache.org/kafka/2.7.0/kafka_2.13-2.7.0.tgz && tar -xvzf kafka_2.13-2.7.0.tgz
WORKDIR /tmp/kafka_2.13-2.7.0

ADD start.sh ./

ENTRYPOINT ["./start.sh"]