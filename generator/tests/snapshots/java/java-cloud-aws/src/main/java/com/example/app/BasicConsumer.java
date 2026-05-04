package com.example.app;

import com.csfleExample.PersonalData;
import io.confluent.kafka.serializers.KafkaAvroDeserializer;
import io.confluent.kafka.serializers.KafkaAvroDeserializerConfig;
import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.List;
import java.util.Properties;

public class BasicConsumer {
    private static final Logger log = LoggerFactory.getLogger(BasicConsumer.class.getName());

    private static Properties getProperties() {
        Properties props = new Properties();
        props.setProperty(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, Config.getBootstrapServers());
        props.setProperty(ConsumerConfig.GROUP_ID_CONFIG, Config.getConsumerGroupId());
        props.setProperty(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.setProperty(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, KafkaAvroDeserializer.class.getName());
        props.setProperty(ConsumerConfig.METRIC_REPORTER_CLASSES_CONFIG, "");
        props.setProperty(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, Config.getAutoOffsetReset());
        props.setProperty("schema.registry.url", Config.getSchemaRegistryUrl());
        // Deserialize back into the generated PersonalData class.
        props.setProperty(KafkaAvroDeserializerConfig.SPECIFIC_AVRO_READER_CONFIG, "true");

        // Confluent Cloud authentication (SASL_SSL + PLAIN).
        props.setProperty("security.protocol", "SASL_SSL");
        props.setProperty("sasl.mechanism", "PLAIN");
        props.setProperty(
            "sasl.jaas.config",
            "org.apache.kafka.common.security.plain.PlainLoginModule required " +
            "username='" + Config.getKafkaSaslUsername() + "' " +
            "password='" + Config.getKafkaSaslPassword() + "';"
        );

        // Schema Registry basic auth (Confluent Cloud).
        props.setProperty("basic.auth.credentials.source", "USER_INFO");
        props.setProperty("schema.registry.basic.auth.user.info", Config.getSchemaRegistryBasicAuthUserInfo());

        // AWS credentials are passed to the encryption rule executor so the
        // AwsKmsDriver can construct an AWSCredentials instance.
        props.setProperty("rule.executors._default_.param.access.key.id", Config.getAwsAccessKeyId());
        props.setProperty("rule.executors._default_.param.secret.access.key", Config.getAwsSecretAccessKey());

        return props;
    }

    public static void main(String[] args) {
        Config.validateConfig();

        final String topic = Config.getTopic();
        final Properties properties = getProperties();

        log.info("Starting consumer on topic: {}", topic);

        Runtime.getRuntime().addShutdownHook(new Thread(() -> log.info("Shutting down consumer")));

        try (Consumer<String, PersonalData> consumer = new KafkaConsumer<>(properties)) {
            consumer.subscribe(List.of(topic));

            while (true) {
                ConsumerRecords<String, PersonalData> records = consumer.poll(Duration.ofMillis(1000));
                for (ConsumerRecord<String, PersonalData> record : records) {
                    PersonalData pd = record.value();
                    String ts = pd.getTimestamp() != null ? pd.getTimestamp().toString() : "<nil>";
                    System.out.printf(
                        "--- Personal Data ---%n" +
                        "  ID:        %s%n" +
                        "  Name:      %s%n" +
                        "  Birthday:  %s%n" +
                        "  Timestamp: %s%n" +
                        "---------------------%n",
                        pd.getId(), pd.getName(), pd.getBirthday(), ts);
                }
            }
        } catch (Exception e) {
            log.error("Consumer error: {}", e.getLocalizedMessage(), e);
        }
    }
}
