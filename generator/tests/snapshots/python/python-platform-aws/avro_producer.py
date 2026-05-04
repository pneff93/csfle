import os
from datetime import datetime, timezone, date

from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.schema_registry.rules.encryption.awskms.aws_driver import AwsKmsDriver
from confluent_kafka.schema_registry.rules.encryption.encrypt_executor import FieldEncryptionExecutor
from confluent_kafka.serialization import MessageField, SerializationContext, StringSerializer
from dateutil.relativedelta import relativedelta

import config


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
    AwsKmsDriver.register()
    FieldEncryptionExecutor.register()
    # AWS credentials are passed via rule.executors._default_.param.* below; this comment
# is kept for parity with other KMS partials.

    schema = "personal_data.avsc"
    path = os.path.realpath(os.path.dirname(__file__))
    with open(f"{path}/avro/{schema}") as f:
        schema_str = f.read()

    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    ser_conf = {'auto.register.schemas': False, 'use.latest.version': True}
    rule_conf = {
        'access.key.id': os.getenv('AWS_ACCESS_KEY_ID'),
        'secret.access.key': os.getenv('AWS_SECRET_ACCESS_KEY'),
    }
    avro_serializer = AvroSerializer(
        schema_registry_client,
        schema_str,
        personal_data_to_dict,
        conf=ser_conf,
        rule_conf=rule_conf,
    )

    string_serializer = StringSerializer('utf_8')

    producer = Producer(producer_conf)

    print("Producing user records to topic {}. ^C to exit.".format(topic))
    i = 0
    while i < 20:
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


# Load configuration from environment variables
config.validate_config()

topic = config.get_topic()
schema_registry_conf = config.get_schema_registry_config()
producer_conf = config.get_producer_config()

if __name__ == '__main__':
    main()
