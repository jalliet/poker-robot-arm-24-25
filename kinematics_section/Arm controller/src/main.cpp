#include <Arduino.h>
#include <Servo.h>
#include <map>

constexpr int MOTOR0_PIN = A9,  MOTOR1_PIN = 1,  MOTOR2_PIN = 2, MOTOR3_PIN = 3;
constexpr int VALVE_MOTOR_PIN = 0, PUMP_MOTOR_PIN = 0;

constexpr int PWM_FREQ = 50;

Servo servo0, servo1, servo2, servo3, servo4;
float angle0, angle1, angle2, angle3, angle4;
bool suck;

auto& btSerial = Serial8;

std::map<String, float> variables;

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
  Serial.printf("my_status %f %f %f %f %f %d %d %f",
    variables["angle0"],
    variables["angle1"],
    variables["angle2"],
    variables["angle3"],
    variables["angle4"],
    variables["suck"] == 0 ? 0 : 1,
    millis
  );
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

  Serial.print("success\n");
}

/*
  String Parsing
*/

// Proccess a command which should be in the form "lhs=float"
void parse_command(String command) {
  Serial.printf("Received command '%s'.\n", command.c_str());


  // Parse the expersion var_name=float

  String lhs;
  String rhs;

  bool success = false;

  for (int i = 0; i < command.length(); i++) {
      if (command[i] == '=') {
          lhs = command.substring(0, i);
          rhs = command.substring(i + 1);

          success = true;
          break;
      }
  }
  

  if (success == false) {
      btSerial.printf("\n>Invalid command\n");
      Serial.printf("\n>Invalid command\n");
      return;
  }


  // Now we have lhs and rhs, set the parameter accordingly
  
  std::map<String, float>::iterator it = variables.find(lhs);
  // Check to see if the paramater actually exists in the map
  if (it == variables.end())  {
      btSerial.printf("\n>Invalid variable %s\n", lhs.c_str());
      Serial.printf("\n>Invalid variable %s\n", lhs.c_str());
      return;
  }
      
  // Convert to float
  char *str_end = rhs.end();
  float val = strtof(rhs.begin(), &str_end);
  if (str_end == rhs.begin()) {
      btSerial.printf("\n>Invalid float\n");
      Serial.printf("\n>Invalid float\n");
      return;
  }
  it->second = val;
  Serial.printf("\n>Successfully changed %s to %f\n", it->first.c_str(), it->second);
  btSerial.printf("\n>Successfully changed %s to %f\n", it->first.c_str(), it->second);
  for (auto it = variables.begin(); it != variables.end(); it++) {
      btSerial.printf("%s = %f,", it->first.c_str(), it->second);
      Serial.printf("%s = %f,", it->first.c_str(), it->second);
  }
  Serial.printf("\n");
  btSerial.printf("\n");
  
}

void setup() {
  
  pinMode(VALVE_MOTOR_PIN, OUTPUT);
  pinMode(PUMP_MOTOR_PIN, OUTPUT);
  
  pinMode(PIN_A9, OUTPUT);
  
  servo0.attach(MOTOR0_PIN, 1000, 2000);
  servo1.attach(MOTOR1_PIN, 1000, 2000);
  servo2.attach(MOTOR2_PIN, 1000, 2000);
  servo3.attach(MOTOR3_PIN, 1000, 2000);
  Serial8.setTimeout(0);
  
  Serial.begin(9600); // USB is always 12 or 480 Mbit/sec
  Serial8.begin(9600, SERIAL_8N1);
  Serial.println("Hello USB");
  btSerial.println("Hello BT");

  variables["delay_ms"] = 0;
  variables["req_status"] = 0;
  variables["status_period"] = 0;
  
  variables["suck"] = 0;
  variables["angle0"] = 0;
  variables["angle1"] = 0;
  variables["angle2"] = 0;
  variables["angle3"] = 0;
  variables["angle4"] = 0;
}

int clamp_angle(float angle) {
  if (angle > 180) angle = 180;
  if (angle < 0) angle = 0;
  return (int) angle
}

void loop() {
  /*
    1) Proccess any commands
  */
  static char buffer[1024];
  size_t length = Serial.readBytesUntil(';', buffer, sizeof(buffer)-1);

  if (length >= 3) {
    buffer[length] = '\0'; // Null terminator
    parse_command(String(buffer));
  }

  /*
    2) Take action on commands
  */

  if (variables["req_status"] != 0) {
    report_status();
    variables["req_status"] = 0;
  }

  if (variables["angle0"] != angle0) {
    angle0 = clamp(variables["angle0"]);
    servo0.write(angle0);
  }

  if (variables["angle1"] != angle0) {
    angle1 = clamp(variables["angle1"]);
    servo1.write(angle1);
  }

  if (variables["angle2"] != angle0) {
    angle2 = clamp(variables["angle2"]);
    servo2.write(angle2);
  }

  if (variables["angle3"] != angle0) {
    angle3 = clamp(variables["angle3"]);
    servo3.write(angle3);
  }

  if (variables["angle4"] != angle0) {
    angle4 = clamp(variables["angle4"]);
    servo4.write(angle4);
  }


  /*
    3) Report data
  */
  if (variables["continous_status"] == 1) {
    report_status();
  }

  /*
   4) Wait
  */
  delay((uint32_t) variables["delay_ms"]);
}