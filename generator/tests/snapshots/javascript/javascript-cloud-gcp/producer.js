const { KafkaJS } = require('@confluentinc/kafka-javascript');
const {
  SchemaRegistryClient,
  AvroSerializer,
  SerdeType,
  FieldEncryptionExecutor,
  GcpKmsDriver,
} = require('@confluentinc/schemaregistry');
const config = require('./config');

FieldEncryptionExecutor.register();
GcpKmsDriver.register();

async function main() {
  config.validate();

  const topic = config.topic();

  const sr = new SchemaRegistryClient({
    baseURLs: [config.schemaRegistryUrl()],
    basicAuthCredentials: {
      credentialsSource: 'USER_INFO',
      userInfo: process.env.SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO,
    },
  });

  const serializer = new AvroSerializer(sr, SerdeType.VALUE, {
    autoRegisterSchemas: false,
    useLatestVersion: true,
    ruleConfig: {
      'client.id': process.env.GCP_CLIENT_ID,
      'client.email': process.env.GCP_CLIENT_EMAIL,
      'private.key.id': process.env.GCP_PRIVATE_KEY_ID,
      'private.key': process.env.GCP_PRIVATE_KEY,
    },
  });

  const kafka = new KafkaJS.Kafka({
    kafkaJS: {
      brokers: [config.bootstrapServers()],
      ssl: true,
      sasl: {
        mechanism: 'plain',
        username: process.env.KAFKA_SASL_USERNAME,
        password: process.env.KAFKA_SASL_PASSWORD,
      },
    },
  });

  const producer = kafka.producer();
  await producer.connect();

  console.log(`Producing user records to topic ${topic}. ^C to exit.`);

  try {
    for (let i = 1; i <= 20; i++) {
      const today = new Date();
      const birthday = new Date(today);
      birthday.setFullYear(today.getFullYear() - i);

      const record = {
        id: String(i),
        name: 'Anna',
        birthday: birthday.toISOString().slice(0, 10),
        timestamp: today.toISOString(),
      };

      try {
        const value = await serializer.serialize(topic, record);
        const result = await producer.send({
          topic,
          messages: [{ key: String(i), value }],
        });
        const r = result[0];
        const offset = r.baseOffset !== undefined ? r.baseOffset : r.offset;
        console.log(
          `PersonalData record ${i} successfully produced to ${r.topicName} [${r.partition}] at offset ${offset}`
        );
      } catch (err) {
        console.error(`Delivery failed for record ${i}: ${err.message}`);
      }
    }
  } finally {
    console.log('\nFlushing records...');
    await producer.disconnect();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
