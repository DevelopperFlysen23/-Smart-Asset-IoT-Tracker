/*
  IoT Project: School Equipment Tracking
  Hardware: ESP32, RC522 (RFID), SW-420 (Vibration), Buzzer
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>

// --- WiFi & MQTT Configuration ---
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "broker.hivemq.com";

// --- Hardware Pins ---
#define SS_PIN 5
#define RST_PIN 22
#define VIBRATION_PIN 34
#define BUZZER_PIN 25

MFRC522 rfid(SS_PIN, RST_PIN);
WiFiClient espClient;
PubSubClient client(espClient);

bool systemArmed = true;

void setup() {
  Serial.begin(115200);
  pinMode(VIBRATION_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  // Initialize SPI and RFID
  SPI.begin();
  rfid.PCD_Init();

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void setup_wifi() {
  delay(10);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi Connected");
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) message += (char)payload[i];

  if (message == "UNLOCK") {
    digitalWrite(BUZZER_PIN, HIGH); delay(200); digitalWrite(BUZZER_PIN, LOW);
  } else if (message == "DISARM") {
    systemArmed = false;
    digitalWrite(BUZZER_PIN, LOW);
  }
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32_SchoolTracker")) {
      client.subscribe("school/control");
    } else {
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  // 1. RFID Detection
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    String uid = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
      uid += String(rfid.uid.uidByte[i] < 0x10 ? "0" : "");
      uid += String(rfid.uid.uidByte[i], HEX);
    }
    uid.toUpperCase();
    Serial.println("RFID detected: " + uid);
    client.publish("school/request", uid.c_str());
    delay(1000);
  }

  // 2. Vibration Detection (if armed)
  if (systemArmed && digitalRead(VIBRATION_PIN) == HIGH) {
    Serial.println("Vibration detected!");
    client.publish("school/alerts", "VIBRATION");
    digitalWrite(BUZZER_PIN, HIGH); // Sound the alarm
    delay(1000);
  }
}
