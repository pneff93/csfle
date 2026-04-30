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

    public static String getKafkaSaslUsername() {
        return getEnvOrThrow("KAFKA_SASL_USERNAME");
    }

    public static String getKafkaSaslPassword() {
        return getEnvOrThrow("KAFKA_SASL_PASSWORD");
    }

    public static String getSchemaRegistryBasicAuthUserInfo() {
        return getEnvOrThrow("SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO");
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
        getKafkaSaslUsername();
        getKafkaSaslPassword();
        getSchemaRegistryBasicAuthUserInfo();
        getAzureKmsKeyId();
        getAzureKmsKeyName();
        getAzureKmsType();
        getAzureTenantId();
        getAzureClientId();
        getAzureClientSecret();
    }
}
