#include <Arduino.h>

void setup() {
  pinMode(0, OUTPUT);
  pinMode(1, OUTPUT);  
  digitalWrite(0, HIGH);
}

void loop() {
  digitalWrite(1, HIGH);
  wait(1000)
  digitalWrite(1, LOW);
  wait(1000)
}
