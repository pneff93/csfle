import com.csfleExample.PersonalData
import com.google.gson.Gson

import org.apache.kafka.clients.producer.KafkaProducer
import org.apache.kafka.clients.producer.ProducerRecord
import org.apache.kafka.clients.producer.RecordMetadata
import org.apache.kafka.common.errors.SerializationException
import org.apache.logging.log4j.kotlin.logger
import java.text.SimpleDateFormat
import java.util.*

class KafkaProducer {

    private val logger = logger(javaClass.name)
    private val gson = Gson()

    fun produceEvents(properties: ProducerProperties, data: List<String>): Thread {

        val thread = Thread {

            val kafkaProducer = KafkaProducer<String, PersonalData>(properties.configureProperties())

            Thread.sleep(10000)
            val target_topic: String = System.getenv("TARGET_TOPIC")
            logger.info("Kafka Producer started, target topic is $target_topic")

            data.forEach { event ->

                val personalData = gson.fromJson(event, PersonalData::class.java)
                personalData.setTimestamp(SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'.'SSS'Z'").format(Date()))

                try {
                    kafkaProducer.send(ProducerRecord("$target_topic", personalData.getId(), personalData),
                    ) { m: RecordMetadata, e: Exception? ->
                        when (e) {
                            null -> logger.info("event produced to ${m.topic()}")
                            else -> logger.error("oh no, error occurred")
                        }
                    }
                } catch ( e: SerializationException){
                    ///logger.error("${e.cause} for $personalData")
                    logger.error("${e.cause} with stack trace ${e.printStackTrace()}")
                }

                Thread.sleep(2000)
            }
        }

        thread.start()
        return thread
    }
}