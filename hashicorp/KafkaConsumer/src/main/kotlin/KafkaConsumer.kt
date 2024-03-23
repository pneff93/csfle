import com.csfleExample.PersonalData
import org.apache.kafka.clients.consumer.KafkaConsumer
import org.apache.kafka.clients.consumer.ConsumerRecords
import org.apache.logging.log4j.kotlin.logger
import java.time.Duration
import java.util.*

class KafkaConsumer {

    private val logger = logger(javaClass.name)

    fun consumeEvents(properties: Properties) {

        val topicName = properties.getProperty("topic.name")
        properties.remove("topic.name")
        val consumer = org.apache.kafka.clients.consumer.KafkaConsumer<String, PersonalData>(properties)
        consumer.subscribe(listOf(topicName))

        while (true) {

            val event: ConsumerRecords<String, PersonalData> = consumer.poll(Duration.ofMillis(100))

            if (!event.isEmpty) {
                event.forEach { logger.info("We consumed the event ${it.value()}") }

            }
        }
    }
}