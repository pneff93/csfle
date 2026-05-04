import os

from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.schema_registry.rules.encryption.azurekms.azure_driver import AzureKmsDriver
from confluent_kafka.schema_registry.rules.encryption.encrypt_executor import FieldEncryptionExecutor
from confluent_kafka.serialization import MessageField, SerializationContext

import config


class PersonalData(object):

    def __init__(self, id, name, birthday, timestamp):
        self.id = id
        self.name = name
        self.birthday = birthday
        self.timestamp = timestamp

    def __str__(self):
        return (f"--- Personal Data ---\n"
                f"  ID:        {self.id}\n"
                f"  Name:      {self.name}\n"
                f"  Birthday:  {self.birthday}\n"
                f"  Timestamp: {self.timestamp}\n"
                f"---------------------")


def dict_to_personal_data(obj, ctx):
    if obj is None:
        return None

    return PersonalData(id=obj["id"], name=obj["name"], birthday=obj["birthday"], timestamp=obj["timestamp"])


def main():
    AzureKmsDriver.register()
    FieldEncryptionExecutor.register()
    # Azure service-principal credentials are passed via rule.executors._default_.param.* below.

    schema_str = None

    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    rule_conf = {
        'tenant.id': os.getenv('AZURE_TENANT_ID'),
        'client.id': os.getenv('AZURE_CLIENT_ID'),
        'client.secret': os.getenv('AZURE_CLIENT_SECRET'),
    }
    avro_deserializer = AvroDeserializer(
        schema_registry_client,
        schema_str,
        dict_to_personal_data,
        rule_conf=rule_conf,
    )

    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])

    while True:
        try:
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            personal_data = avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
            if personal_data is not None:
                print(personal_data)
        except KeyboardInterrupt:
            break

    consumer.close()


# Load configuration from environment variables
config.validate_config()

topic = config.get_topic()
schema_registry_conf = config.get_schema_registry_config()
consumer_conf = config.get_consumer_config()

if __name__ == '__main__':
    main()
