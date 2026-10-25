/**
 * ESP8266 Wi-Fi Bridge for STM32 Smart Parking Hub
 *
 * Receives JSON telemetry string from STM32 over Hardware Serial (115200 baud)
 * and forwards it as an HTTP POST request to the FastAPI backend.
 *
 * Board: Generic ESP8266 Module / NodeMCU / Wemos D1 Mini
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Replace with your laptop's local IPv4 address (run `ipconfig` in cmd to find it)
const char* serverUrl = "http://192.168.1.100:8000/api/telemetry";

WiFiClient client;
HTTPClient http;

void setup() {
  Serial.begin(115200);
  delay(100);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void loop() {
  // Listen for incoming telemetry JSON payload from STM32 over UART
  if (Serial.available()) {
    String payload = Serial.readStringUntil('\n');
    payload.trim();

    if (payload.startsWith("{\"readings\":") && WiFi.status() == WL_CONNECTED) {
      http.begin(client, serverUrl);
      http.addHeader("Content-Type", "application/json");

      int httpResponseCode = http.POST(payload);
      if (httpResponseCode > 0) {
        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);
      } else {
        Serial.print("Error code: ");
        Serial.println(httpResponseCode);
      }
      http.end();
    }
  }
}
