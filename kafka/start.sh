#! /bin/sh -xe
LISTENERS=PLAINTEXT://localhost:9092
if [ "$KAFKA_ADVERTISED_LISTENERS" != "" ]; then
  LISTENERS=$KAFKA_ADVERTISED_LISTENERS
fi

echo advertised.listeners=$LISTENERS >> config/server.properties
sh -c "bin/zookeeper-server-start.sh config/zookeeper.properties &" && bin/kafka-server-start.sh config/server.properties