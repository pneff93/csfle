

fun main() {

    val kafkaConsumer = KafkaConsumer()
    val properties = ConsumerProperties()

    kafkaConsumer.consumeEvents(properties)
}