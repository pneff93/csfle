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

    fun produceEvents(properties: Properties, data: List<String>): Thread {

        val thread = Thread {

            val topicName = properties.getProperty("topic.name")
            properties.remove("topic.name")
            val kafkaProducer = KafkaProducer<String, PersonalData>(properties)

            Thread.sleep(10000)
            logger.info("Kafka Producer started")

            data.forEach { event ->

                val personalData = gson.fromJson(event, PersonalData::class.java)
                personalData.setTimestamp(SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'.'SSS'Z'").format(Date()))

                try {
                    kafkaProducer.send(ProducerRecord(topicName, personalData.getId(), personalData),
                    ) { m: RecordMetadata, e: Exception? ->
                        when (e) {
                            null -> logger.info("event produced to ${m.topic()}")
                            else -> logger.error("oh no, error occurred")
                        }
                    }
                } catch ( e: SerializationException){
                    logger.error("${e.cause} for $personalData")
                }

                Thread.sleep(2000)
            }
        }

        thread.start()
        return thread
    }
}