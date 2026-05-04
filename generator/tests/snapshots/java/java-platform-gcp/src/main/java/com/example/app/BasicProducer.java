package com.example.app;

import com.csfleExample.PersonalData;
import io.confluent.kafka.serializers.KafkaAvroSerializer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.StringSerializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.Properties;

public class BasicProducer {

    private static final Logger log = LoggerFactory.getLogger(BasicProducer.class);

    private static Properties getProperties() {
        Properties props = new Properties();
        props.setProperty(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, Config.getBootstrapServers());
        props.setProperty(ProducerConfig.CLIENT_ID_CONFIG, "my-platform-gcp-java-client-producer");
        props.setProperty(ProducerConfig.ACKS_CONFIG, "all");
        props.setProperty(ProducerConfig.RETRIES_CONFIG, "10");
        props.setProperty(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.setProperty(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, KafkaAvroSerializer.class.getName());
        props.setProperty(ProducerConfig.METRIC_REPORTER_CLASSES_CONFIG, "");
        props.setProperty("schema.registry.url", Config.getSchemaRegistryUrl());
        props.setProperty("auto.register.schemas", "false");
        props.setProperty("use.latest.version", "true");

        // GCP service-account fields are passed to the encryption rule executor so
        // the GcpKmsDriver can construct service-account credentials.
        props.setProperty("rule.executors._default_.param.client.id", Config.getGcpClientId());
        props.setProperty("rule.executors._default_.param.client.email", Config.getGcpClientEmail());
        props.setProperty("rule.executors._default_.param.private.key.id", Config.getGcpPrivateKeyId());
        props.setProperty("rule.executors._default_.param.private.key", Config.getGcpPrivateKey());

        return props;
    }

    public static void main(String[] args) {
        Config.validateConfig();

        final String topic = Config.getTopic();
        final Properties properties = getProperties();

        log.info("Producing user records to topic {}", topic);

        try (Producer<String, PersonalData> producer = new KafkaProducer<>(properties)) {

            for (int i = 1; i <= 20; i++) {
                PersonalData personalData = new PersonalData();
                personalData.setId(String.valueOf(i));
                personalData.setName("Anna");
                personalData.setBirthday(LocalDate.now()
                    .minusYears(i)
                    .format(DateTimeFormatter.ofPattern("yyyy-MM-dd")));
                personalData.setTimestamp(OffsetDateTime.now(ZoneOffset.UTC).toString());

                ProducerRecord<String, PersonalData> record =
                    new ProducerRecord<>(topic, String.valueOf(i), personalData);

                final int recordNumber = i;
                producer.send(record, (metadata, e) -> {
                    if (e != null) {
                        log.error("Delivery failed for record {}: {}", recordNumber, e.getLocalizedMessage());
                        return;
                    }
                    log.info("PersonalData record {} successfully produced to {} [{}] at offset {}",
                        recordNumber, metadata.topic(), metadata.partition(), metadata.offset());
                });
            }

            producer.flush();
            log.info("Flushed all records");
        } catch (Exception e) {
            log.error("Producer error: {}", e.getLocalizedMessage(), e);
            throw e;
        }
    }
}
