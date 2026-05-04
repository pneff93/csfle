package com.example.app;

import io.github.cdimascio.dotenv.Dotenv;

public class Config {
    private static final Dotenv dotenv = Dotenv.configure()
        .directory(".")
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

    public static String getConsumerGroupId() {
        return getEnvOrThrow("KAFKA_GROUP_ID");
    }

    public static String getAutoOffsetReset() {
        return getEnvOrThrow("KAFKA_AUTO_OFFSET_RESET");
    }

    public static String getHcVaultKmsKeyId() {
        return getEnvOrThrow("HCVAULT_KMS_KEY_ID");
    }

    public static String getHcVaultKmsKeyName() {
        return getEnvOrThrow("HCVAULT_KMS_KEY_NAME");
    }

    public static String getHcVaultKmsType() {
        return getEnvOrThrow("HCVAULT_KMS_TYPE");
    }

    public static String getVaultAddr() {
        return getEnvOrThrow("VAULT_ADDR");
    }

    public static String getVaultToken() {
        return getEnvOrThrow("VAULT_TOKEN");
    }

    private static String getEnvOrThrow(String key) {
        String value = dotenv.get(key);
        if (value == null) {
            throw new IllegalStateException(
                "Missing required configuration: " + key + "\n" +
                "Edit .env to set this value."
            );
        }
        return value;
    }

    public static void validateConfig() {
        getTopic();
        getBootstrapServers();
        getSchemaRegistryUrl();
        getConsumerGroupId();
        getAutoOffsetReset();
        getHcVaultKmsKeyId();
        getHcVaultKmsKeyName();
        getHcVaultKmsType();
        getVaultAddr();
        getVaultToken();
    }
}
