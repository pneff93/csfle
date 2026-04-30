package com.example.app;

import org.apache.kafka.clients.admin.Admin;
import org.apache.kafka.clients.admin.AdminClientConfig;
import org.apache.kafka.clients.admin.NewTopic;
import org.apache.kafka.common.errors.TopicExistsException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Properties;
import java.util.concurrent.ExecutionException;

/**
 * Idempotent topic-creation helper. Run from bootstrap.sh via:
 *   mvn -q exec:java -Dexec.mainClass="com.example.app.BootstrapTopic"
 */
public class BootstrapTopic {

    private static final Logger log = LoggerFactory.getLogger(BootstrapTopic.class);
    private static final short REPLICATION_FACTOR = 3;
    private static final int NUM_PARTITIONS = 1;

    private static Properties getProperties() {
        Properties props = new Properties();
        props.setProperty(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, Config.getBootstrapServers());

        // Confluent Cloud authentication (SASL_SSL + PLAIN).
        props.setProperty("security.protocol", "SASL_SSL");
        props.setProperty("sasl.mechanism", "PLAIN");
        props.setProperty(
            "sasl.jaas.config",
            "org.apache.kafka.common.security.plain.PlainLoginModule required " +
            "username='" + Config.getKafkaSaslUsername() + "' " +
            "password='" + Config.getKafkaSaslPassword() + "';"
        );
        return props;
    }

    public static void main(String[] args) {
        Config.validateConfig();
        final String topic = Config.getTopic();

        try (Admin admin = Admin.create(getProperties())) {
            NewTopic newTopic = new NewTopic(topic, NUM_PARTITIONS, REPLICATION_FACTOR);
            admin.createTopics(List.of(newTopic)).all().get();
            log.info("Created topic {}", topic);
        } catch (ExecutionException e) {
            if (e.getCause() instanceof TopicExistsException) {
                log.info("Topic {} already exists", Config.getTopic());
            } else {
                log.error("Failed to create topic: {}", e.getCause().getLocalizedMessage(), e.getCause());
                System.exit(1);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("Interrupted while creating topic", e);
            System.exit(1);
        }
    }
}
