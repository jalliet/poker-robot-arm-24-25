#include <Arduino.h>
#include <Servo.h>

constexpr int MOTOR0_PIN = 0,  MOTOR1_PIN = 1,  MOTOR2_PIN = 2, MOTOR3_PIN = 3;
constexpr int VALVE_MOTOR_PIN = 0, PUMP_MOTOR_PIN = 0;

constexpr int PWM_FREQ = 50;

float current_angle0, current_angle1, current_angle2, current_angle3, current_speed;

bool reporting_status_periodically = false;
float status_period = 1;


Servo servo0, servo1, servo2, servo3;


/*
  Commands
*/



void enable_suction() {
  digitalWrite(VALVE_MOTOR_PIN, 1);
  digitalWrite(PUMP_MOTOR_PIN, 1);
}

void disable_suction() {
  digitalWrite(VALVE_MOTOR_PIN, 0);
  digitalWrite(PUMP_MOTOR_PIN, 0);
}

void report_status() {
  Serial.println("my_status ");
}

void set_pin(int pin, bool value) {
  pinMode(pin, OUTPUT);
  digitalWrite(pin, value ? 1:0);
}



void set_angles(
  float angle0, float angle1, float angle2, float angle3,
  float speed0, float speed1, float speed2, float speed3) {

  if (angle0 < 0 || angle0 > 180) return;
  servo0.write(int(angle0));

  if (angle1 < 0 || angle1 > 180) return;
  servo1.write(int(angle1));

  if (angle2 < 0 || angle2 > 180) return;
  servo2.write(int(angle2));

  if (angle3 < 0 || angle3 > 180) return;
  servo3.write(int(angle3));
}

/*
  Proccessing the space seperated words
*/

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

  if (length == 2 && messages[0] == "set_pin") {
    bool value = messages[1] == '1';
    int pin = messages[0].toInt();

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

/*
  String Parsing
*/

void parse_line(const String& line) {
  constexpr int MAX_MESSAGES = 32;
  String messages[MAX_MESSAGES];
  int message_count = 0;
  int last_space = 0;
  for (int i = 0; i < line.length(); i++) {
    if (line[i] == ' ') {
      messages[message_count] = line.substring(last_space, i);
      last_space = i;
      message_count++;
      if (message_count >= MAX_MESSAGES) {
        Serial.println("error The message is too long");
        return;
      }
    }
  }

  received_message(messages, message_count);

}

void setup() {
  Serial.begin(9600); // USB is always 12 or 480 Mbit/sec
  while (!Serial) {
    // wait for Arduino Serial Monitor to be ready
  }

  pinMode(VALVE_MOTOR_PIN, OUTPUT);
  pinMode(PUMP_MOTOR_PIN, OUTPUT);

  pinMode(PIN_A9, OUTPUT);

  servo0.attach(MOTOR0_PIN, 1000, 2000);
  servo1.attach(MOTOR1_PIN, 1000, 2000);
  servo2.attach(MOTOR2_PIN, 1000, 2000);
  servo3.attach(MOTOR3_PIN, 1000, 2000);
}

void loop() {
  digitalWrite(PIN_A9, 1);

  delay(500);
  digitalWrite(PIN_A9, 0);

  delay(500);
  

  //String str = Serial.readStringUntil('\n', 500);
  //parse_line(str);
}
