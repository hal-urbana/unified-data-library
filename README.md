# Unified Data Library (UDL)

A Kafka-based message broker for unified data communication across systems.

## Overview

The Unified Data Library (UDL) serves as a central message broker using Apache Kafka to facilitate data exchange between various systems. It provides a standardized, scalable, and fault-tolerant infrastructure for message publishing and consumption.

## Architecture

### Kafka Cluster
- **Broker Mode**: KRaft (without ZooKeeper)
- **Replication**: Multi-browser replication across availability zones
- **Partitioning**: Configurable partition counts based on throughput requirements
- **Retention**: Time-based and size-based retention policies

### Core Components
1. **Producers**: Applications that publish messages to Kafka topics
2. **Consumers**: Applications that subscribe to and process messages
3. **Consumer Groups**: Horizontal scaling for parallel message processing
4. **Schema Registry**: Enforces data contracts using Apache Avro/Protobuf/JSON Schema
5. **Dead Letter Queues (DLQ)**: Handles unprocessable messages

## Topic Design

### Naming Convention
Follow the pattern: `{domain}.{entity}.{event}`

Examples:
- `geometry.feature.created`
- `knowledge.document.updated`
- `analytics.metrics.processed`

### Partition Strategy
- Determine partition count based on expected throughput
- Consider message ordering requirements (same key → same partition)
- Balance between parallelism and overhead

## Message Schema

### Recommended Formats
- **Apache Avro**: Binary format, schema evolution support
- **Protocol Buffers**: Binary format, multi-language support
- **JSON Schema**: Human-readable, flexible validation

### Example Schema Structure
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "eventId": {"type": "string", "format": "uuid"},
    "timestamp": {"type": "string", "format": "date-time"},
    "source": {"type": "string"},
    "payload": {"type": "object"}
  },
  "required": ["eventId", "timestamp", "source", "payload"]
}
```

## Producer Configuration

```yaml
# producer-config.yaml
bootstrap.servers: ["kafka-broker-1:9092", "kafka-broker-2:9092"]
acks: all
retries: 3
retry.backoff.ms: 1000
compression.type: snappy
max.in.flight.requests.per.connection: 5
enable.idempotence: true
```

## Consumer Configuration

```yaml
# consumer-config.yaml
bootstrap.servers: ["kafka-broker-1:9092", "kafka-broker-2:9092"]
group.id: my-consumer-group
auto.offset.reset: earliest
enable.auto.commit: false
isolation.level: read_committed
```

## Error Handling

### Producer Error Handling
- Implement exponential backoff for transient failures
- Use retry mechanisms with maximum retry limits
- Log failed messages with context

### Consumer Error Handling
- **Dead Letter Queue (DLQ)**: Route unprocessable messages to a separate topic
- **Retry Strategy**: Limited retries for transient processing errors
- **Circuit Breaker**: Temporarily pause processing on repeated failures

## Monitoring

### Key Metrics
- **Consumer Lag**: Delay between message production and consumption
- **Broker Health**: CPU, memory, disk usage
- **Network Throughput**: Messages/sec, bytes/sec
- **Under-Replicated Partitions**: Partitions without full replication
- **Error Rates**: Failed produces/consumes

### Recommended Tools
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Kafka Manager**: Cluster monitoring and management
- **Confluent Control Center**: Comprehensive Kafka monitoring

## Security

### Encryption
- **In Transit**: TLS/SSL for all broker-client communication
- **At Rest**: Encryption of data on disk

### Authentication
- **SASL/SCRAM**: Username/password authentication
- **SASL/PLAIN**: Simple authentication (less secure)
- **mTLS**: Mutual TLS for certificate-based authentication

### Authorization
- **Access Control Lists (ACLs)**: Fine-grained permissions
- **Role-Based Access Control (RBAC)**: Role-based permissions
- **Topic-Level Permissions**: Control read/write access per topic

### Example ACLs
```bash
# Grant read access to consumer group
kafka-acls --bootstrap-server kafka-broker:9092 --add --allow-principal User:consumer-user --operation Read --topic my-topic

# Grant write access to producer
kafka-acls --bootstrap-server kafka-broker:9092 --add --allow-principal User:producer-user --operation Write --topic my-topic
```

## Deployment

### Prerequisites
- Java 11+ (for Kafka brokers)
- Docker (for containerized deployment)
- Kubernetes (for scalable deployment)

### Quick Start with Docker

```bash
# Start Kafka cluster with docker-compose
docker-compose up -d

# Create a test topic
docker exec kafka-broker kafka-topics --bootstrap-server kafka-broker:9092 --create --topic test-topic --partitions 3 --replication-factor 2
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  kafka-broker:
    image: confluentinc/cp-kafka:7.4.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_INTERNAL:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092,PLAINTEXT_INTERNAL://kafka-broker:29092
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_NODE_ID: 1
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka-broker:29093
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,PLAINTEXT_INTERNAL://0.0.0.0:29092,CONTROLLER://0.0.0.0:29093
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT_INTERNAL
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LOG_DIRS: /tmp/kraft-combined-logs
    volumes:
      - ./kafka-data:/tmp/kraft-combined-logs
```

## Testing

### Producer Test
```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['kafka-broker:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

producer.send('test-topic', value={'message': 'Hello, UDL!'})
producer.flush()
```

### Consumer Test
```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'test-topic',
    bootstrap_servers=['kafka-broker:9092'],
    auto_offset_reset='earliest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

for message in consumer:
    print(f"Received: {message.value}")
```

## Performance Optimization

### Producer Optimization
- Batch messages using `linger.ms` and `batch.size`
- Use compression (`snappy`, `lz4`, `zstd`)
- Tune `max.in.flight.requests.per.connection` for throughput vs ordering

### Consumer Optimization
- Tune `fetch.min.bytes` and `fetch.max.wait.ms` for batch fetching
- Adjust `max.partition.fetch.bytes` based on message sizes
- Use multiple consumer instances in a consumer group

##Troubleshooting

### Common Issues
- **High Consumer Lag**: Increase consumer instances or partition count
- **Under-Replicated Partitions**: Check broker health and network connectivity
- **Producer Timeouts**: Increase `request.timeout.ms` or check broker availability
- **Schema Incompatibility**: Verify schema compatibility before producing

## Project Timeline

- **2026-04-09**: Initial project setup and architecture definition.
- **2026-04-12**: David Trepp confirmed the exact project name as "Unified Data Library" and verified it as a message broker using Kafka. Awaiting host endpoints and authentication details.

## Host Endpoints and Authentication
- **Endpoints**: [Awaiting confirmation from David Trepp]
- **Authentication**: [Awaiting confirmation from David Trepp]

## Research & Domain Context
Based on confirmed requirements, the Unified Data Library (UDL) acts as a centralized Kafka-based message backbone. 

### Key Advantages
1. **Durability**: Guaranteed message persistence via distributed logs.
2. **Scalability**: Horizontal scaling through partitioning.
3. **Decoupling**: Independent evolution of producers and consumers.
4. **Replayability**: Support for re-processing historical data streams.

## Next Steps

1. [ ] Receive host endpoints from David Trepp
2. [ ] Receive authentication information
3. [ ] Configure Kafka client with provided credentials
4. [ ] Test connectivity to Kafka cluster
5. [ ] Define initial topic structure
6. [ ] Implement producer/consumer examples
7. [ ] Set up monitoring and alerting

## Resources

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Confluent Kafka Documentation](https://docs.confluent.io/)
- [Kafka Best Practices](https://www.confluent.io/blog/apache-kafka-best-practices/)
