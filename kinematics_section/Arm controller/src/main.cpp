#include <Arduino.h>
#include <Servo.h>

constexpr int MOTOR0_PIN = A9,  MOTOR1_PIN = 1,  MOTOR2_PIN = 2, MOTOR3_PIN = 3;
constexpr int VALVE_MOTOR_PIN = 0, PUMP_MOTOR_PIN = 0;
constexpr int Serial8_RX = 34,  Serial8_TX = 35;

constexpr int PWM_FREQ = 50;



float current_angle0, current_angle1, current_angle2, current_angle3, current_angle4, current_speed;

bool reporting_status_periodically = false;
float status_period = 1;


Servo servo0, servo1, servo2, servo3, servo4;


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
  Serial8.println("my_status ");
}

void set_pin(int pin, bool value) {
  pinMode(pin, OUTPUT);
  digitalWrite(pin, value ? 1:0);
}



void set_angles(
  float angle0, float angle1, float angle2, float angle3, float angle4,
  float speed0, float speed1, float speed2, float speed3, float speed4) {

  if (angle0 < 0 || angle0 > 180) return;
  servo0.write(int(angle0));

  if (angle1 < 0 || angle1 > 180) return;
  servo1.write(int(angle1));

  if (angle2 < 0 || angle2 > 180) return;
  servo2.write(int(angle2));

  if (angle3 < 0 || angle3 > 180) return;
  servo3.write(int(angle3));

  if (angle4 < 0 || angle4 > 180) return;
  servo4.write(int(angle4));

  Serial8.print("success\n");
}

/*
  Proccessing the space seperated words
*/

void received_message(const String* messages, int length) {
  printf("%d;\n", length);
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

  else if (length == 2 && messages[0] == "set_pin") {
    bool value = messages[1] == '1';
    int pin = messages[0].toInt();

  }

  else if (length == 2 && messages[0] == "req_periodic_status") {
    float period = messages[1].toFloat();
    if (period == 0) {}
  }

  else if (length == 9 && messages[0] == "set_angles") {
    set_angles(
      messages[1].toFloat(), 
      messages[2].toFloat(), 
      messages[3].toFloat(), 
      messages[4].toFloat(), 
      messages[5].toFloat(),
      messages[6].toFloat(), 
      messages[7].toFloat(), 
      messages[8].toFloat(), 0,0);
  }
  else {
    Serial8.print("Invalid command\n");
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
        Serial8.println("error The message is too long");
        return;
      }
    }
  }

  received_message(messages, message_count);

}

void setup() {
  Serial.begin(9600); // USB is always 12 or 480 Mbit/sec
  while (!Serial8) {
    // wait for Arduino Serial8 Monitor to be ready
  }

  pinMode(VALVE_MOTOR_PIN, OUTPUT);
  pinMode(PUMP_MOTOR_PIN, OUTPUT);

  pinMode(PIN_A9, OUTPUT);

  servo0.attach(MOTOR0_PIN, 1000, 2000);
  servo1.attach(MOTOR1_PIN, 1000, 2000);
  servo2.attach(MOTOR2_PIN, 1000, 2000);
  servo3.attach(MOTOR3_PIN, 1000, 2000);
  Serial8.setTimeout(0);
  
}

void processIncomingByte(char c) {
  Serial8.printf("Recieved %c\n", c);
  static char buffer[512];
  static int size = 0;
  buffer[size] = c;
  size++;
  if (size == 511) {
    size = 0;
    Serial8.print("buffer overun");
  }

  if ( c == ';') {
    buffer[size] = '\0';
    String str {buffer};
    parse_line(str);
    size = 0;
  }
}

void loop() {
    while (Serial8.available () > 0){
      processIncomingByte (Serial8.read ());
      Serial.println("reading next byte");
    }

    String str = Serial8.readStringUntil('\n');
    parse_line(str);
    Serial.println(str);
    Serial.println("reading...");
}


    /*
    digitalWrite(PIN_A9, 1);

    Serial8.println("sekjdhhfgkj");
    delay(500);
    digitalWrite(PIN_A9, 0);

    delay(500);
    */