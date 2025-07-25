import kotlinx.serialization.*
import kotlinx.serialization.json.*

// Example data class with serialization
@Serializable
data class Person(
    val name: String,
    val age: Int,
    val email: String? = null
)

@Serializable
data class Company(
    val name: String,
    val employees: List<Person>
)

fun main() {
    // Create sample data
    val person1 = Person("John Doe", 30, "john@example.com")
    val person2 = Person("Jane Smith", 25)
    val company = Company("Tech Corp", listOf(person1, person2))
    
    // Serialize to JSON
    val jsonString = Json.encodeToString(company)
    println("Serialized JSON:")
    println(jsonString)
    
    // Deserialize from JSON
    val jsonInput = """
        {
            "name": "Another Company",
            "employees": [
                {"name": "Bob", "age": 35, "email": "bob@example.com"},
                {"name": "Alice", "age": 28}
            ]
        }
    """.trimIndent()
    
    val deserializedCompany = Json.decodeFromString<Company>(jsonInput)
    println("\nDeserialized object:")
    println("Company: ${deserializedCompany.name}")
    deserializedCompany.employees.forEach { employee ->
        println("  - ${employee.name}, age ${employee.age}, email: ${employee.email ?: "N/A"}")
    }
    
    // Working with JSON elements directly
    val jsonElement = Json.parseToJsonElement(jsonInput)
    val companyName = jsonElement.jsonObject["name"]?.jsonPrimitive?.content
    println("\nCompany name from JsonElement: $companyName")
}