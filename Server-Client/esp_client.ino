#include <ESP8266WiFi.h> // shit you need for wifi 
#include <ArduinoWebsockets.h> // other shit for you need for websocket client

char *ssid="wifi ssid here"; //wifi conf
char *password="wifi password here"; //wifi conf
char *deviceName="device name / room name here"; //device roomName/hostname/mdns (same for all)

int sensorPin= 1; // default sensor pin no need to modify here

const char* serverHost="websocket server ip address"; //Enter server address
const char* connPassword="auth password you can find it in server code"; // websocket connection password
uint16_t serverPort=9000; // Enter server port

using namespace websockets; 
WebsocketsClient client; //websocket client object
bool oldDataState;
unsigned long currentMillis;
unsigned int prevMillis;

void setup() {
    Serial.begin(115200); // if you have the esp device connected you can see data in the Serial Monitor
    pinMode(sensorPin,INPUT); // initialize sensor pin as input
    WiFi.mode(WIFI_STA);  // start esp in station mode

    WiFi.begin(ssid, password);  // connect to wifi with the wifi credentials 
    while(WiFi.status() != WL_CONNECTED){ // try connecting to wifi until connected or timeout
      digitalWrite(LED_BUILTIN, HIGH); delay(250); digitalWrite(LED_BUILTIN, LOW); // blink blue led on esp
      Serial.print("."); // print in console .
    }
    Serial.println(WiFi.localIP()); // print local ip
   
    client.addHeader("Devicename",deviceName); // add the deviceName inside the websocket header
    client.addHeader("Authpassword",connPassword);   
}

// this function runs seccond in a loop
void loop() {
  currentMillis = millis(); // get current runtime miliseccond 
  if(client.available()) { // if esp connected to websocket server
      client.poll(); // check for new messages from server   
      int SensorData = digitalRead(sensorPin); // read data from sensor/pin         
      if(SensorData != oldDataState){ // if sensor state changed then send data to server            
          oldDataState = SensorData;
          String docString = "{\"SensorData\":"+String(SensorData)+"}";
          Serial.println(docString);
          client.send(docString); // send data to websocket server
      }      
  }else{ // else try to connect to websocket server every seccond
        if (currentMillis - prevMillis >= 1000) { // non blocking timer using current runtime miliseccond 
            prevMillis = currentMillis;
            Serial.println("Server "+String(serverHost)+" is not online");                     
            if(client.connect(serverHost, serverPort, "/")) // connect to websocket server    
                client.send("{\"SensorData\":"+String(digitalRead(sensorPin))+"}"); // if connected send a initial message to websocket server             
            digitalWrite(LED_BUILTIN,LOW); delay(10); digitalWrite(LED_BUILTIN,HIGH);         
        }
  }
  
}
