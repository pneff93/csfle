// Loads CSFLE demo configuration from the shared `.env` file used by the
// Python, Java, Go, and .NET clients (lives in confluent_platform/aws/.env).
//
// `dotenv` is non-clobbering by default — variables already exported in the
// shell take precedence over values in `.env`. This is what makes the
// unauthorized-access `export AWS_SECRET_ACCESS_KEY=invalid_secret_key` trick
// in the README work.

const fs = require('fs');
const path = require('path');

for (const candidate of ['../.env', '../../.env', '.env']) {
  const resolved = path.resolve(candidate);
  if (fs.existsSync(resolved)) {
    require('dotenv').config({ path: resolved, quiet: true });
    break;
  }
}

function get(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `Missing required configuration: ${name}\n` +
      `Please set it in ../.env (see ../.env.example).`
    );
  }
  return value;
}

function validate() {
  const required = [
    'KAFKA_TOPIC',
    'KAFKA_BOOTSTRAP_SERVERS',
    'KAFKA_GROUP_ID',
    'KAFKA_AUTO_OFFSET_RESET',
    'SCHEMA_REGISTRY_URL',
    'AWS_KMS_KEY_NAME',
    'AWS_KMS_TYPE',
    'AWS_KMS_KEY_ID',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
  ];
  for (const name of required) get(name);
}

module.exports = {
  validate,
  topic: () => get('KAFKA_TOPIC'),
  bootstrapServers: () => get('KAFKA_BOOTSTRAP_SERVERS'),
  groupId: () => get('KAFKA_GROUP_ID'),
  autoOffsetReset: () => get('KAFKA_AUTO_OFFSET_RESET'),
  schemaRegistryUrl: () => get('SCHEMA_REGISTRY_URL'),

  // AWS credentials packaged for AvroSerializer/Deserializer `ruleConfig`.
  // The Confluent JS AWS KMS driver reads `access.key.id` and `secret.access.key`
  // from the rule config and passes them straight to the AWS SDK. Passing them
  // explicitly is more reliable across environments than relying on the SDK's
  // default credential chain.
  awsRuleConfig: () => ({
    'access.key.id': get('AWS_ACCESS_KEY_ID'),
    'secret.access.key': get('AWS_SECRET_ACCESS_KEY'),
  }),
};
