#!/usr/bin/env python3
"""
Unified Data Library - Python Kafka Consumer Example

This example demonstrates how to consume and process messages from a Kafka topic
using the Unified Data Library (UDL) infrastructure.
"""

import json
import signal
import sys
from datetime import datetime, timezone
from kafka import KafkaConsumer
from kafka.errors import KafkaError


class UDLConsumer:
    """Kafka Consumer for Unified Data Library."""
    
    def __init__(self, bootstrap_servers, group_id, client_id="udl-consumer"):
        """
        Initialize the UDL Consumer.
        
        Args:
            bootstrap_servers: List of Kafka broker addresses
            group_id: Consumer group identifier
            client_id: Client identifier for this consumer
        """
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.client_id = client_id
        self.consumer = None
        self.running = False
        
    def connect(self, topics, **consumer_config):
        """
        Connect to Kafka cluster and subscribe to topics.
        
        Args:
            topics: List of topics to subscribe to
            **consumer_config: Additional Kafka consumer configuration
        """
        config = {
            'bootstrap_servers': self.bootstrap_servers,
            'group_id': self.group_id,
            'client_id': self.client_id,
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': False,  # Manual commit for better reliability
            'isolation_level': 'read_committed',
            'value_deserializer': lambda x: json.loads(x.decode('utf-8')) if x else None,
            **consumer_config
        }
        
        try:
            self.consumer = KafkaConsumer(*topics, **config)
            print(f"✓ Connected to Kafka cluster: {self.bootstrap_servers}")
            print(f"✓ Subscribed to topics: {topics}")
            print(f"✓ Consumer group: {self.group_id}")
            return True
        except KafkaError as e:
            print(f"✗ Failed to connect or subscribe: {e}")
            return False
    
    def start(self, handler_callback):
        """
        Start consuming messages.
        
        Args:
            handler_callback: Function to call for each message: func(message_value, partition, offset)
        """
        if not self.consumer:
            raise RuntimeError("Consumer not connected. Call connect() first.")
        
        self.running = True
        print("\n--- Listening for messages (Press Ctrl+C to stop) ---")
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                
                # Metadata
                topic = message.topic
                partition = message.partition
                offset = message.offset
                
                print(f"\n[Received] Topic: {topic} | Partition: {partition} | Offset: {offset}")
                
                # Extract UDL specific headers if present or body
                msg_val = message.value
                
                try:
                    # Process the message
                    handler_callback(msg_val, partition, offset)
                    
                    # Commit offset after successful processing
                    self.consumer.commit()
                    print(f"✓ Offset {offset} committed")
                except Exception as e:
                    print(f"✗ Error processing message at offset {offset}: {e}")
                    # In production, check if we should route to DLQ or halt
                    
        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
        finally:
            self.close()
            
    def stop(self):
        """Signal the consumer to stop."""
        self.running = False
        
    def close(self):
        """Close the consumer connection."""
        if self.consumer:
            self.consumer.close()
            print(f"✓ Closed consumer connection")


def message_handler(data, partition, offset):
    """Example message handler."""
    if not data:
        print("Empty message received")
        return
        
    print(f"--- UDL Message Breakdown ---")
    print(f"Event ID:  {data.get('eventId', 'N/A')}")
    print(f"Timestamp: {data.get('timestamp', 'N/A')}")
    print(f"Source:    {data.get('source', 'N/A')}")
    print(f"Domain:    {data.get('domain', 'N/A')}")
    print(f"Entity:    {data.get('entity', 'N/A')}")
    print(f"Payload:   {json.dumps(data.get('payload', {}), indent=2)}")


# Example Usage
if __name__ == "__main__":
    # Configuration - replace with UDL host endpoints
    BOOTSTRAP_SERVERS = ["kafka_broker_address:9092"]
    TOPIC = "udl.test.messages"
    GROUP = "udl-example-group"
    
    print("=" * 60)
    print("UDL Consumer Example")
    print("=" * 60)
    
    consumer = UDLConsumer(BOOTSTRAP_SERVERS, GROUP)
    
    # Handle signals
    def signal_handler(sig, frame):
        consumer.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if consumer.connect([TOPIC]):
        consumer.start(message_handler)
    else:
        print("Failed to connect. Check your Kafka configuration.")
        exit(1)
