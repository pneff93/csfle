import os

from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.schema_registry.rules.encryption.azurekms.azure_driver import AzureKmsDriver
from confluent_kafka.schema_registry.rules.encryption.encrypt_executor import FieldEncryptionExecutor
from confluent_kafka.serialization import MessageField, SerializationContext


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

    schema_str = None

    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    avro_deserializer = AvroDeserializer(schema_registry_client, schema_str, dict_to_personal_data)

    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])

    while True:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            personal_data = avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
            if personal_data is not None:
                # print the personal data record
                print(personal_data)
        except KeyboardInterrupt:
            break

    consumer.close()


# Topic
topic = 'csfle-demo'

# 👇 SR URL and <SR API Key:SR API Secret>
schema_registry_conf = {
    'url': 'SR_URL',
    'basic.auth.user.info': 'SR_API_KEY:SR_API_SECRET'
}

# 👇 Bootstrap URL, Kafka API Key, Kafka API Secret
consumer_conf = {
    'bootstrap.servers': 'KAFKA_URL',
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': 'KAFKA_API_KEY',
    'sasl.password': 'KAFKA_API_SECRET',
    'auto.offset.reset': "earliest",
    'group.id': 'csfle-demo-consumer-group',
}

# 👇 Tenant ID of the registered app
os.environ['AZURE_TENANT_ID'] = 'TENANT_ID'

# 👇 Client ID of the registered app
os.environ['AZURE_CLIENT_ID'] = 'CLIENT_ID'

# 👇 Client secret value
os.environ['AZURE_CLIENT_SECRET'] = 'SECRET'

if __name__ == '__main__':
    main()
