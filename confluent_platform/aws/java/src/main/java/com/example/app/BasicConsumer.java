package com.example.app;

import io.confluent.kafka.serializers.KafkaAvroDeserializer;
import org.apache.kafka.clients.consumer.*;
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
        props.setProperty("schema.registry.url", Config.getSchemaRegistryUrl());
        props.setProperty(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, Config.getAutoOffsetReset());
        props.setProperty("rule.executors._default_.param.access.key.id", Config.getAwsAccessKeyId());
        props.setProperty("rule.executors._default_.param.secret.access.key", Config.getAwsSecretAccessKey());
        return props;
    }

    public static void main(String[] args) {
        Config.validateConfig();

        final String topic = Config.getTopic();
        final Properties properties = getProperties();
        log.info("Starting consumer");

        try (Consumer<String, generated.PersonalData> consumer = new KafkaConsumer<>(properties)) {

            log.info("Configured consumer");

            consumer.subscribe(List.of(topic));

            log.info("Consumer subscribed to the topic: {}", topic);

            while (true) {
                ConsumerRecords<String, generated.PersonalData> records = consumer.poll(Duration.ofMillis(1000));

                if (records.count() > 0) {

                    log.info("Receveid {} records", records.count());

                    for (ConsumerRecord<String, generated.PersonalData> consumerRecord : records) {
                        log.info("Consumed message: key={}, value={}, partition={}, offset={}",
                                consumerRecord.key(), consumerRecord.value(), consumerRecord.partition(), consumerRecord.offset());
                    }
                    System.out.println("Bye");
                    log.info("Bye");
                    break;

                }

            }

        } catch (Exception e) {
            log.warn("Error while checking daily message count: {}", e.getLocalizedMessage());
        }
    }
}
