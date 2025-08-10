# Task: HTTP Server

Create a simple HTTP server in Scala.

The server should:
- Listen on the specified port
- Handle GET requests at "/"
- Return the expected response

Example structure using Akka HTTP:
```scala
import akka.actor.typed.ActorSystem
import akka.actor.typed.scaladsl.Behaviors
import akka.http.scaladsl.Http
import akka.http.scaladsl.model._
import akka.http.scaladsl.server.Directives._
import scala.concurrent.ExecutionContext
import scala.util.{Failure, Success}

object Main {
  def main(args: Array[String]): Unit = {
    implicit val system = ActorSystem(Behaviors.empty, "http-server")
    implicit val executionContext: ExecutionContext = system.executionContext
    
    val port = 8080 // Or get from environment/arguments
    
    val route = 
      path("") {
        get {
          complete(HttpEntity(ContentTypes.`text/plain(UTF-8)`, "Response content"))
        }
      }
    
    val bindingFuture = Http().newServerAt("localhost", port).bind(route)
    
    bindingFuture.onComplete {
      case Success(binding) =>
        println(s"Server online at http://localhost:$port/")
      case Failure(e) =>
        println(s"Server failed to start: ${e.getMessage}")
        system.terminate()
    }
  }
}
```

Note: You may also use other HTTP frameworks like http4s or Play Framework.