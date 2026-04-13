#!/usr/bin/env python3
"""
Unified Data Library - Python Kafka Producer Example

This example demonstrates how to publish messages to a Kafka topic
using the Unified Data Library (UDL) infrastructure.
"""

import json
import uuid
import time
from datetime import datetime, timezone
from kafka import KafkaProducer
from kafka.errors import KafkaError


class UDLCProducer:
    """Kafka Producer for Unified Data Library."""
    
    def __init__(self, bootstrap_servers, client_id="udl-producer"):
        """
        Initialize the UDL Producer.
        
        Args:
            bootstrap_servers: List of Kafka broker addresses
            client_id: Client identifier for this producer
        """
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.producer = None
        
    def connect(self, **producer_config):
        """
        Connect to Kafka cluster with specified configuration.
        
        Args:
            **producer_config: Additional Kafka producer configuration
        """
        config = {
            'bootstrap_servers': self.bootstrap_servers,
            'client_id': self.client_id,
            'acks': 'all',  # Ensure message durability
            'retries': 3,  # Number of retries on failure
            'retry_backoff_ms': 1000,  # Wait 1 second between retries
            'compression_type': 'snappy',  # Use compression for efficiency
            'max_in_flight_requests_per_connection': 5,
            'enable_idempotence': True,
            'value_serializer': lambda v: json.dumps(v, default=str).encode('utf-8'),
            **producer_config
        }
        
        try:
            self.producer = KafkaProducer(**config)
            print(f"✓ Connected to Kafka cluster: {self.bootstrap_servers}")
            return True
        except KafkaError as e:
            print(f"✗ Failed to connect to Kafka: {e}")
            return False
    
    def publish(self, topic, payload, key=None, domain="udl", entity="message"):
        """
        Publish a message to a Kafka topic.
        
        Args:
            topic: Kafka topic name
            payload: Message payload (dict)
            key: Optional message key for partitioning
            domain: Domain for message context
            entity: Entity type for message context
        
        Returns:
            Future object representing the send operation
        """
        if not self.producer:
            raise RuntimeError("Producer not connected. Call connect() first.")
        
        message = {
            'eventId': str(uuid.uuid4()),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': self.client_id,
            'domain': domain,
            'entity': entity,
            'payload': payload
        }
        
        try:
            if key:
                future = self.producer.send(topic, key=key.encode('utf-8'), value=message)
            else:
                future = self.producer.send(topic, value=message)
            
            print(f"✓ Published message to topic '{topic}': eventId={message['eventId']}")
            return future
        except KafkaError as e:
            print(f"✗ Failed to publish message to topic '{topic}': {e}")
            raise
    
    def publish_batch(self, topic, messages):
        """
        Publish a batch of messages to a Kafka topic.
        
        Args:
            topic: Kafka topic name
            messages: List of message dicts with 'payload' and optional 'key'
        
        Returns:
            List of Future objects
        """
        if not self.producer:
            raise RuntimeError("Producer not connected. Call connect() first.")
        
        futures = []
        for msg in messages:
            message = {
                'eventId': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': self.client_id,
                'domain': msg.get('domain', 'udl'),
                'entity': msg.get('entity', 'message'),
                'payload': msg['payload']
            }
            
            try:
                if 'key' in msg:
                    future = self.producer.send(
                        topic, 
                        key=msg['key'].encode('utf-8'), 
                        value=message
                    )
                else:
                    future = self.producer.send(topic, value=message)
                
                futures.append(future)
                print(f"✓ Queued message for topic '{topic}': eventId={message['eventId']}")
            except KafkaError as e:
                print(f"✗ Failed to queue message: {e}")
                raise
        
        return futures
    
    def flush(self, timeout=10):
        """Flush all outstanding messages."""
        if self.producer:
            self.producer.flush(timeout=timeout)
            print(f"✓ Flushed all messages")
    
    def close(self):
        """Close the producer connection."""
        if self.producer:
            self.flush()
            self.producer.close()
            print(f"✓ Closed producer connection")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Example Usage
if __name__ == "__main__":
    # Configuration - replace with UDL host endpoints
    BOOTSTRAP_SERVERS = ["kafka-broker-1:9092", "kafka-broker-2:9092"]
    TOPIC = "udl.test.messages"
    
    print("=" * 60)
    print("UDL Producer Example")
    print("=" * 60)
    
    # Create and connect producer
    with UDLCProducer(BOOTSTRAP_SERVERS, client_id="example-producer") as producer:
        if not producer.connect():
            print("Failed to connect. Check your Kafka configuration.")
            exit(1)
        
        # Publish a single message
        print("\n--- Publishing Single Message ---")
        message = {
            'content': 'Hello, Unified Data Library!',
            'priority': 'normal'
        }
        future = producer.publish(
            topic=TOPIC,
            payload=message,
            key='test-key-1',
            domain='udl',
            entity='test'
        )
        
        # Publish a batch of messages
        print("\n--- Publishing Batch ---")
        batch_messages = [
            {'key': 'batch-1', 'payload': {'text': 'First batch message'}},
            {'key': 'batch-2', 'payload': {'text': 'Second batch message'}},
            {'payload': {'text': 'Third batch message (no key)'}}
        ]
        futures = producer.publish_batch(TOPIC, batch_messages)
        
        # Wait for all messages to be sent
        print("\n--- Waiting for delivery ---")
        for future in futures + [future]:
            future.get(timeout=10)
        
        print("\n✓ All messages published successfully!")