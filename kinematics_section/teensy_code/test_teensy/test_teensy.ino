#include <Arduino.h>

void setup() {
  Serial.begin(9600); // USB is always 12 or 480 Mbit/sec
  while (!Serial) {
    // wait for Arduino Serial Monitor to be ready
  }


}

void received_message(const char* message, int length) {
    
}

void loop() {
  
}
