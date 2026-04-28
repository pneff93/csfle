const { KafkaJS } = require('@confluentinc/kafka-javascript');
const {
  SchemaRegistryClient,
  AvroDeserializer,
  SerdeType,
  FieldEncryptionExecutor,
  AwsKmsDriver,
} = require('@confluentinc/schemaregistry');
const config = require('./config');

FieldEncryptionExecutor.register();
AwsKmsDriver.register();

async function main() {
  config.validate();

  const topic = config.topic();

  const sr = new SchemaRegistryClient({
    baseURLs: [config.schemaRegistryUrl()],
  });

  const deserializer = new AvroDeserializer(sr, SerdeType.VALUE, {
    ruleConfig: config.awsRuleConfig(),
  });

  const kafka = new KafkaJS.Kafka({
    kafkaJS: {
      brokers: [config.bootstrapServers()],
    },
  });

  const consumer = kafka.consumer({
    kafkaJS: {
      groupId: config.groupId(),
      fromBeginning: config.autoOffsetReset() === 'earliest',
    },
  });

  await consumer.connect();
  await consumer.subscribe({ topic });

  let shuttingDown = false;
  const shutdown = async (signal) => {
    if (shuttingDown) return;
    shuttingDown = true;
    console.log(`\nCaught ${signal}: terminating`);
    try {
      await consumer.disconnect();
    } finally {
      process.exit(0);
    }
  };
  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));

  await consumer.run({
    eachMessage: async ({ message }) => {
      try {
        const record = await deserializer.deserialize(topic, message.value);
        const ts = record.timestamp ?? '<nil>';
        console.log(
          `--- Personal Data ---\n` +
          `  ID:        ${record.id}\n` +
          `  Name:      ${record.name}\n` +
          `  Birthday:  ${record.birthday}\n` +
          `  Timestamp: ${ts}\n` +
          `---------------------`
        );
      } catch (err) {
        console.error(`Failed to deserialize: ${err.message}`);
      }
    },
  });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
