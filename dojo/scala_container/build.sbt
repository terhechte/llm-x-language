name := "scala-container"

version := "1.0.0"

scalaVersion := "2.13.10"

libraryDependencies ++= Seq(
  // JSON processing with Circe
  "io.circe" %% "circe-core" % "0.14.5",
  "io.circe" %% "circe-generic" % "0.14.5",
  "io.circe" %% "circe-parser" % "0.14.5",
  
  // HTTP client with STTP
  "com.softwaremill.sttp.client3" %% "core" % "3.9.0",
  
  // HTTP server with Akka HTTP
  "com.typesafe.akka" %% "akka-http" % "10.5.2",
  "com.typesafe.akka" %% "akka-stream" % "2.8.4",
  "com.typesafe.akka" %% "akka-actor-typed" % "2.8.4",
  
  // Logging
  "ch.qos.logback" % "logback-classic" % "1.4.11"
)

// Scala compiler options
scalacOptions ++= Seq(
  "-deprecation",
  "-feature",
  "-unchecked"
)

// Run settings
run / fork := true
run / connectInput := true