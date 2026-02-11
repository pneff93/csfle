import os
from datetime import datetime, timezone, date
from uuid import uuid4

from confluent_kafka import Producer
from confluent_kafka.schema_registry import Rule, RuleKind, RuleMode, RuleParams, RuleSet, Schema, SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.schema_registry.rules.encryption.azurekms.azure_driver import AzureKmsDriver
from confluent_kafka.schema_registry.rules.encryption.encrypt_executor import FieldEncryptionExecutor
from confluent_kafka.serialization import MessageField, SerializationContext, StringSerializer
from dateutil.relativedelta import relativedelta


class PersonalData(object):

    def __init__(self, id, name, birthday, timestamp):
        self.id = id
        self.name = name
        self.birthday = birthday
        self.timestamp = timestamp


def personal_data_to_dict(data, ctx):
    return dict(
        id=data.id,
        name=data.name,
        birthday=data.birthday,
        timestamp=data.timestamp
    )


def delivery_report(err, msg):
    if err is not None:
        print("Delivery failed for record {}: {}".format(msg.key(), err))
        return
    print(
        'PersonalData record {} successfully produced to {} [{}] at offset {}'.format(
            msg.key(), msg.topic(), msg.partition(), msg.offset()
        )
    )


def main():
    AzureKmsDriver.register()
    FieldEncryptionExecutor.register()

    schema = "personal_data.avsc"
    path = os.path.realpath(os.path.dirname(__file__))
    with open(f"{path}/avro/{schema}") as f:
        schema_str = f.read()

    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    subject = f"{topic}-value"
    schema_registry_client.register_schema(subject, Schema(schema_str, "AVRO", [], None))

    ser_conf = {'auto.register.schemas': False, 'use.latest.version': True}
    avro_serializer = AvroSerializer(schema_registry_client, schema_str, personal_data_to_dict, conf=ser_conf)

    string_serializer = StringSerializer('utf_8')

    producer = Producer(producer_conf)

    print("Producing user records to topic {}. ^C to exit.".format(topic))
    i = 0
    while i < 20:
        # Serve on_delivery callbacks from previous calls to produce()
        i = i + 1
        producer.poll(0.0)
        try:
            personal_data = PersonalData(
                id=str(i),
                name='Anna',
                birthday=(date.today() - relativedelta(years=i)).strftime('%Y-%m-%d'),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            producer.produce(
                topic=topic,
                key=string_serializer(str(i)),
                value=avro_serializer(personal_data, SerializationContext(topic, MessageField.VALUE)),
                on_delivery=delivery_report,
            )
        except KeyboardInterrupt:
            break
        except ValueError:
            print("Invalid input, discarding record...")
            continue

    print("\nFlushing records...")
    producer.flush()


# define the topic
topic = 'csfle-demo'

# name the KEK
kek_name = f'{topic}-kek'
kms_type = 'azure-kms'

# 👇 that's the Azure Key Identifier of the key you created in Azure Key Vault
kms_key_id = 'Azure Key Identifier'

# 👇 SR URL and <SR API Key:SR API Secret>
schema_registry_conf = {
    'url': 'SR_URL',
    'basic.auth.user.info': 'SR_API_KEY:SR_API_SECRET'
}

# 👇 Bootstrap URL, Kafka API Key, Kafka API Secret
producer_conf = {
    'bootstrap.servers': 'KAFKA_URL', # provide this
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': 'KAFKA_API_KEY', # provide this
    'sasl.password': 'KAFKA_API_SECRET' #provide this
}

# 👇 Tenant ID of the registered app
os.environ['AZURE_TENANT_ID'] = 'TENANT_ID'

# 👇 Client ID of the registered app
os.environ['AZURE_CLIENT_ID'] = 'CLIENT_ID'

# 👇 Client secret value
os.environ['AZURE_CLIENT_SECRET'] = 'SECRET'

if __name__ == '__main__':
    main()
