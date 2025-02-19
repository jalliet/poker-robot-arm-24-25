#include <Arduino.h>

constexpr int MOTOR0_PIN = 0,  MOTOR1_PIN = 1,  MOTOR2_PIN = 2, MOTOR3_PIN = 3;
constexpr int VALVE_MOTOR_PIN = 0, PUMP_MOTOR_PIN = 0;

float current_angle0, current_angle1, current_angle2, current_angle3, current_speed;

bool reporting_status_periodically = false;
float status_period = 1;

void setup() {
  Serial.begin(9600); // USB is always 12 or 480 Mbit/sec
  while (!Serial) {
    // wait for Arduino Serial Monitor to be ready
  }

  pinMode(MOTOR0_PIN, OUTPUT);
  pinMode(MOTOR1_PIN, OUTPUT);
  pinMode(MOTOR2_PIN, OUTPUT);
  pinMode(MOTOR3_PIN, OUTPUT);

  pinMode(VALVE_MOTOR_PIN, OUTPUT);
  pinMode(PUMP_MOTOR_PIN, OUTPUT);
}

void enable_suction() {

}

void disable_suction() {

}

void report_status() {
  Serial.println("my_status " + )
}

void set_angles(
  float angle0, float angle1, float angle2, float angle3,
  float speed0, float speed1, float speed2, float speed3) {

}


void received_message(const String* messages, int length) {
  if (length == 1) {
    if (messages[0] == "suck") {
      enable_suction();
    }
    else if (messages[0] == "suck") {
      disable_suction();
    }
    else if (messages[0] == "req_status") {
      report_status();
    }
  }

  if (length == 2 && messages[0] == "req_periodic_status") {
    float period = messages[1].toFloat();
    if (period == 0) {}
  }

  if (length == 9 && messages[0] == "set_angles") {
    set_angles(
      messages[1].toFloat(), 
      messages[2].toFloat(), 
      messages[3].toFloat(), 
      messages[4].toFloat(), 
      messages[5].toFloat(),
      messages[6].toFloat(), 
      messages[7].toFloat(), 
      messages[8].toFloat());
  }

}

void loop() {
  
}
