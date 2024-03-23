
import kotlin.system.exitProcess
import com.csfleExample.PersonalData
import kotlinx.coroutines.runBlocking

fun main(args: Array<String>) {

    if (args.size != 1) {
        println("Usage: java <producer.jar> <client.properties>")
        exitProcess(0)
    }
    val kafkaProducer = KafkaProducer()
    val properties = ProducerProperties.getProperties(args[0])

    val sensorData = PersonalData::class.java.getResource("/personalData.txt").readText().split("\n")

    runBlocking {

        while (true) {

            val threadKafkaProducer = kafkaProducer.produceEvents(properties, sensorData)
            threadKafkaProducer.join()
        }
    }
}
