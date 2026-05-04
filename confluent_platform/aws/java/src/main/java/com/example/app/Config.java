package com.example.app;

import io.github.cdimascio.dotenv.Dotenv;

public class Config {
    private static final Dotenv dotenv = Dotenv.configure()
        .directory("../")  // Load from parent directory (aws/) — relative to mvn cwd (aws/java)
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

    public static String getAwsKmsKeyId() {
        return getEnvOrThrow("AWS_KMS_KEY_ID");
    }

    public static String getAwsKmsKeyName() {
        return getEnvOrThrow("AWS_KMS_KEY_NAME");
    }

    public static String getAwsKmsType() {
        return getEnvOrThrow("AWS_KMS_TYPE");
    }

    public static String getAwsAccessKeyId() {
        return getEnvOrThrow("AWS_ACCESS_KEY_ID");
    }

    public static String getAwsSecretAccessKey() {
        return getEnvOrThrow("AWS_SECRET_ACCESS_KEY");
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
                "Please create a .env file based on .env.example in the aws/ directory"
            );
        }
        return value;
    }

    public static void validateConfig() {
        getTopic();
        getBootstrapServers();
        getSchemaRegistryUrl();
        getAwsKmsKeyId();
        getAwsKmsKeyName();
        getAwsKmsType();
        getAwsAccessKeyId();
        getAwsSecretAccessKey();
        getConsumerGroupId();
        getAutoOffsetReset();
    }
}
