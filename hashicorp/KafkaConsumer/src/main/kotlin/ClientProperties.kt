
import java.util.*
import java.io.File
import java.io.FileInputStream

object ClientProperties {

    fun readPropertiesFromFile(propertiesFileName: String) : Properties {
        val file = File(propertiesFileName)
        var properties = Properties()
        FileInputStream(file).use { properties.load(it) }
        return properties
    }
}
