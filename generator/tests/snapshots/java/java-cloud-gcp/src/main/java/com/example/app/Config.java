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

    public static String getGcpKmsKeyId() {
        return getEnvOrThrow("GCP_KMS_KEY_ID");
    }

    public static String getGcpKmsKeyName() {
        return getEnvOrThrow("GCP_KMS_KEY_NAME");
    }

    public static String getGcpKmsType() {
        return getEnvOrThrow("GCP_KMS_TYPE");
    }

    public static String getGcpClientId() {
        return getEnvOrThrow("GCP_CLIENT_ID");
    }

    public static String getGcpClientEmail() {
        return getEnvOrThrow("GCP_CLIENT_EMAIL");
    }

    public static String getGcpPrivateKeyId() {
        return getEnvOrThrow("GCP_PRIVATE_KEY_ID");
    }

    public static String getGcpPrivateKey() {
        // dotenv-java doesn't expand `\n` escapes inside .env values like python-dotenv does,
        // so a private key copied from a service-account JSON file (where newlines are encoded
        // as the two-character sequence `\` + `n`) reaches us unchanged. Convert here so the
        // GCP auth library sees a real PEM with newlines.
        return getEnvOrThrow("GCP_PRIVATE_KEY").replace("\\n", "\n");
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
        getGcpKmsKeyId();
        getGcpKmsKeyName();
        getGcpKmsType();
        getGcpClientId();
        getGcpClientEmail();
        getGcpPrivateKeyId();
        getGcpPrivateKey();
    }
}
