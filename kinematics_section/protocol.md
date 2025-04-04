# Commands

# PC => MCU

Comamnds are sent in this format:
```
var1=2.3;var2=3.0;
```
Newlines ('\n' or '\r') are ignored.

| Variable | Description |
| -------- | ------- |
| angleN   | Set the angle of the Nth servo e.g (angle0=90.0)  |
| suck     | Set to 0 to stop sucking the card, set to 1 to suck     |
| | |
| req_status | Set to 1 to report the status, automatically set to 0 after |
| delay_ms| Add delay to the control loop |
| status_period | The status will be reported every `status_period` loop iterations. A value below 1 will disable periodic status |




# MCU => PC
All of these functions are void functions

`my_status <angle0> <angle1> <angle2> <angle3> <are motors moving? (1/0)> <suction status (1/0)> <time (ms)>\n`
sends status of everything to pc

`error <message>\n`
sends error message to pc

`info <message>\n`
