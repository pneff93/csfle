package com.example.app;

import io.github.cdimascio.dotenv.Dotenv;

/**
 * Loads CSFLE demo configuration. Reads ../.env (the shared azure/.env file)
 * via dotenv-java if present, falling back to System.getenv otherwise — so
 * exporting variables in the shell with `set -a; source ../.env; set +a` also
 * works (and is what makes the unauthorized-access test in the README behave
 * correctly).
 */
public class Config {
    private static final Dotenv dotenv = Dotenv.configure()
        .directory("../")  // Load from parent directory (azure/)
        .ignoreIfMissing()
        .load();

    public static String getTopic() {
        return getEnvOrThrow("KAFKA_TOPIC");
    }

    public static String getBootstrapServers() {
        return getEnvOrThrow("KAFKA_BOOTSTRAP_SERVERS");
    }

    public static String getSchemaRegistryUrl() {
        return getEnvOrThrow("SCHEMA_REGISTRY_URL");
    }

    public static String getAzureKmsKeyId() {
        return getEnvOrThrow("AZURE_KMS_KEY_ID");
    }

    public static String getAzureKmsKeyName() {
        return getEnvOrThrow("AZURE_KMS_KEY_NAME");
    }

    public static String getAzureKmsType() {
        return getEnvOrThrow("AZURE_KMS_TYPE");
    }

    public static String getAzureTenantId() {
        return getEnvOrThrow("AZURE_TENANT_ID");
    }

    public static String getAzureClientId() {
        return getEnvOrThrow("AZURE_CLIENT_ID");
    }

    public static String getAzureClientSecret() {
        return getEnvOrThrow("AZURE_CLIENT_SECRET");
    }

    public static String getConsumerGroupId() {
        return getEnvOrThrow("KAFKA_GROUP_ID");
    }

    public static String getAutoOffsetReset() {
        return getEnvOrThrow("KAFKA_AUTO_OFFSET_RESET");
    }

    private static String getEnvOrThrow(String key) {
        String value = dotenv.get(key);
        if (value == null) {
            throw new IllegalStateException(
                "Missing required configuration: " + key + "\n" +
                "Please create a .env file based on .env.example in the azure/ directory"
            );
        }
        return value;
    }

    public static void validateConfig() {
        getTopic();
        getBootstrapServers();
        getSchemaRegistryUrl();
        getAzureKmsKeyId();
        getAzureKmsKeyName();
        getAzureKmsType();
        getAzureTenantId();
        getAzureClientId();
        getAzureClientSecret();
        getConsumerGroupId();
        getAutoOffsetReset();
    }
}
