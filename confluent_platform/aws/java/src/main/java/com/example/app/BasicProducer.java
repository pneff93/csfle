package com.example.app;

import io.confluent.kafka.serializers.KafkaAvroSerializer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.StringSerializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Properties;

public class BasicProducer {

    private static final Logger log = LoggerFactory.getLogger(BasicProducer.class);

    private static Properties getProperties() {
        Properties props = new Properties();
        props.setProperty(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, Config.getBootstrapServers());
        props.setProperty(ProducerConfig.CLIENT_ID_CONFIG, "MY_CLIENT");
        props.setProperty(ProducerConfig.ACKS_CONFIG, "all");
        props.setProperty(ProducerConfig.RETRIES_CONFIG, "10");
        props.setProperty(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.setProperty(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, KafkaAvroSerializer.class.getName());
        props.setProperty(ProducerConfig.METRIC_REPORTER_CLASSES_CONFIG, "");
        props.setProperty("schema.registry.url", Config.getSchemaRegistryUrl());
        props.setProperty("rule.executors._default_.param.access.key.id", Config.getAwsAccessKeyId());
        props.setProperty("rule.executors._default_.param.secret.access.key", Config.getAwsSecretAccessKey());

        return props;
    }

    public static void main(String[] args) {
        Config.validateConfig();

        final String topic = Config.getTopic();
        final Properties properties = getProperties();

        try (Producer<String, generated.PersonalData> producer = new KafkaProducer<>(properties)) {

            for (int counter = 0; counter < 10; counter++) {
                generated.PersonalData personalData = new generated.PersonalData();
                personalData.setId(String.valueOf(counter));
                personalData.setName("Anna");
                personalData.setBirthday(LocalDate.now()
                        .minusYears(counter)
                        .format(DateTimeFormatter.ofPattern("yyyy-MM-dd")));
                personalData.setTimestamp(LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd")));
                ProducerRecord<String, generated.PersonalData> record = new ProducerRecord<>(topic, String.valueOf(counter), personalData);

                producer.send(record, ((recordMetadata, e) -> {
                    if (e != null) {
                        log.error("Failed to send record: {}", e.getLocalizedMessage());
                        return;
                    }
                    log.info("Topic: {} - Partition {}", record.topic(), record.value());
                }));
                sleep();
            }
        } catch (Exception e) {
            log.error("Something went sideways: {}", e.getLocalizedMessage());
            throw e;
        }
    }

    private static void sleep() {
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.warn("Thread Sleep interrupted: {}", e.getLocalizedMessage());
        }
    }
}
