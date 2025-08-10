name := "scala-container"

version := "1.0.0"

scalaVersion := "2.13.10"

libraryDependencies ++= Seq(
  // Basic dependencies - add more as needed
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