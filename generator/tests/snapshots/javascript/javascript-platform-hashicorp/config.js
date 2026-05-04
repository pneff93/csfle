// Loads CSFLE demo configuration from this project's `.env` file.
//
// `dotenv` is non-clobbering by default — variables already exported in the
// shell take precedence over values in `.env`. That's what makes the
// "unauthorized access" trick in the README (`export AWS_SECRET_ACCESS_KEY=invalid`)
// work for testing decryption failures.

const path = require('path');

require('dotenv').config({ path: path.resolve(__dirname, '.env'), quiet: true });

function get(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `Missing required configuration: ${name}\n` +
      `Please set it in .env (see .env.example).`
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
    'HCVAULT_KMS_KEY_NAME',
    'HCVAULT_KMS_TYPE',
    'HCVAULT_KMS_KEY_ID',
    'VAULT_ADDR',
    'VAULT_TOKEN',
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
};
