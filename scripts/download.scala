import java.net.{URLConnection, URL}
import scala.xml._

val url = new URL("http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20html%20where%20url%3D%22http%3A%2F%2Fwww.upenn.edu%2Fregistrar%2Froster%2F%22%20and%20xpath%3D%22%2F%2Ftd%5B%40class%3D'body'%5D%2Fa%22&diagnostics=false")

val conn = url.openConnection

val xml = XML.load(conn.getInputStream)

// link: (xml\\"query"\"results"\"a")(0).attribute("href").get.toString
// name: (xml\\"query"\"results"\"a")(0).text

val subjects = (xml\\"query"\"results"\"a").map( (x) => (x.attribute("href").get.toString, x.text.replaceAll("\\s+", " ")))

subjects.foreach( (x) => {
  println(x)
  try {
    val url = new URL("http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20html%20where%20url%3D%22http%3A%2F%2Fwww.upenn.edu%2Fregistrar%2Froster%2F" + x._1 + "%22%20and%20xpath%3D%22%2F%2Fpre%22")

    val xml = XML.load(url.openConnection.getInputStream)

    val outfile = new java.io.FileWriter(x._1.split('.')(0) + ".txt")
    outfile.write(x._2 + "\n")
    outfile.write((xml\\"results"\\"pre").text)
    outfile.close
  }
  catch {
    case e: Exception => 
  }
})
  

