// Loads CSFLE demo configuration from the shared `.env` file used by the
// Python client (lives in confluent_platform/azure/.env).
//
// `dotenv` is non-clobbering by default — variables already exported in the
// shell take precedence over values in `.env`. This is what makes the
// unauthorized-access `export AZURE_CLIENT_SECRET=invalid_secret_key` trick
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
    'AZURE_KMS_KEY_NAME',
    'AZURE_KMS_TYPE',
    'AZURE_KMS_KEY_ID',
    'AZURE_TENANT_ID',
    'AZURE_CLIENT_ID',
    'AZURE_CLIENT_SECRET',
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

  // Azure service-principal credentials packaged for AvroSerializer/Deserializer
  // `ruleConfig`. The Confluent JS Azure KMS driver reads `tenant.id`, `client.id`,
  // `client.secret` and constructs a ClientSecretCredential. Passing them
  // explicitly is more reliable than relying on Azure SDK defaults.
  azureRuleConfig: () => ({
    'tenant.id': get('AZURE_TENANT_ID'),
    'client.id': get('AZURE_CLIENT_ID'),
    'client.secret': get('AZURE_CLIENT_SECRET'),
  }),
};
