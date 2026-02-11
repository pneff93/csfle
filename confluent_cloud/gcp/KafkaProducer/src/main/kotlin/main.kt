
import com.csfleExample.PersonalData
import kotlinx.coroutines.runBlocking

fun main() {

    val kafkaProducer = KafkaProducer()
    val properties = ProducerProperties()

    val sensorData = PersonalData::class.java.getResource("/personalData.txt").readText().split("\n")

    runBlocking {

        while (true) {

            val threadKafkaProducer = kafkaProducer.produceEvents(properties, sensorData)
            threadKafkaProducer.join()
        }
    }
}