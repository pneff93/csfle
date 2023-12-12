import kotlin.system.exitProcess
import com.csfleExample.PersonalData
import kotlinx.coroutines.runBlocking

fun main(args: Array<String>) {

    if (args.size != 1) {
        println("Usage: java KafkaConsumer-standalone.jar <client.properties>")
        exitProcess(0)
    }
    val kafkaConsumer = KafkaConsumer()
    val properties = ConsumerProperties.getProperties(args[0])

    kafkaConsumer.consumeEvents(properties)
}
