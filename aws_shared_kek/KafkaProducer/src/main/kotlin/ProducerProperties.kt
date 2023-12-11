import org.apache.kafka.clients.CommonClientConfigs
import org.apache.kafka.clients.producer.ProducerConfig
import org.apache.kafka.common.config.SaslConfigs
import org.apache.logging.log4j.kotlin.logger
import java.util.*
import java.lang.System;

class ProducerProperties {

    private val logger = logger(javaClass.name)

    fun configureProperties() : Properties{

        val settings = Properties()
        settings.setProperty(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, "org.apache.kafka.common.serialization.StringSerializer")
        settings.setProperty(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, "io.confluent.kafka.serializers.KafkaAvroSerializer")

        val api_key: String = System.getenv("CC_API_KEY") ?: "<CC Cluster API Key>"
        val api_secret: String = System.getenv("CC_API_SECRET") ?: "<CC Cluster API Secret>"
        val broker_boostrap: String = System.getenv("CC_BOOTSRAP_SERVER") ?: "<CC Cluster Bootstrap>"
        val schema_registry_url: String = System.getenv("SR_URL") ?: "<CC Schema Registry URL>"
        val schema_registry_credentials: String = System.getenv("SR_CRED") ?: "<CC Schema Register Api Key:Secret>"
        /*
        Uncomment this if you want to try the non-shared KEK flow, in this scenario the clients requires KMS access

        val aws_api_key: String = System.getenv("AWS_ACCESS_KEY_ID") ?: "<AWS_ACCESS_KEY_ID>"
        val aws_api_secret: String = System.getenv("AWS_SECRET_ACCESS_KEY") ?: "AWS_SECRET_ACCESS_KEY>"

         // Encryption + AWS Credentials
        settings.setProperty("rule.executors._default_.param.access.key.id", $aws_api_key)
        settings.setProperty("rule.executors._default_.param.secret.access.key", $aws_api_secret)

         */

        settings.setProperty(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "$broker_boostrap")
        settings.setProperty(CommonClientConfigs.SECURITY_PROTOCOL_CONFIG, "SASL_SSL")
        settings.setProperty(SaslConfigs.SASL_MECHANISM, "PLAIN")
        settings.setProperty(SaslConfigs.SASL_JAAS_CONFIG, "org.apache.kafka.common.security.plain.PlainLoginModule required username='$api_key' password='$api_secret';")


        settings.setProperty("schema.registry.url", "$schema_registry_url")
        settings.setProperty("basic.auth.credentials.source", "USER_INFO")
        settings.setProperty("schema.registry.basic.auth.user.info", "$schema_registry_credentials")

        // Required since we manually create schemas
        settings.setProperty("use.latest.version", "true")
        settings.setProperty("auto.register.schemas","false")


        settings.stringPropertyNames()
                .associateWith {settings.getProperty(it)}
                .forEach { logger.info(String.format("%s", it)) }
        return settings
    }
}