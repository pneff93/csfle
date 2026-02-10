import com.csfleExample.PersonalData
import org.apache.kafka.clients.consumer.ConsumerRecords
import org.apache.logging.log4j.kotlin.logger
import java.time.Duration


class KafkaConsumer {

    private val logger = logger(javaClass.name)

    fun consumeEvents(properties: ConsumerProperties) {

        val consumer = org.apache.kafka.clients.consumer.KafkaConsumer<String, PersonalData>(properties.configureProperties())
        val target_topic: String = System.getenv("TARGET_TOPIC")
        val consumer_group: String = System.getenv("TARGET_CONSUMER_GROUP")
        logger.info("Kafka Consumer started, target topic is $target_topic, consumer group is $consumer_group")
        consumer.subscribe(listOf("$target_topic"))

        while (true) {

            val event: ConsumerRecords<String, PersonalData> = consumer.poll(Duration.ofMillis(100))

            if (!event.isEmpty) {
                event.forEach { logger.info("We consumed the event ${it.value()}") }

            }
        }
    }
}