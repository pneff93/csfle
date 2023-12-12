import org.apache.kafka.clients.CommonClientConfigs
import org.apache.kafka.clients.producer.ProducerConfig
import org.apache.kafka.common.config.SaslConfigs
import java.util.*

object ProducerProperties {

    fun getProperties(propertiesFileName: String) : Properties{
        var properties = ClientProperties.readPropertiesFromFile(propertiesFileName)
        properties.setProperty(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, "org.apache.kafka.common.serialization.StringSerializer")
        properties.setProperty(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, "io.confluent.kafka.serializers.KafkaAvroSerializer")

        return properties
    }
}
