# Commands

# PC => MCU

`set_pin <pin> <(True/False)>`
Sets the desired pin to true or false

`set_angles <angle0> <angle1> <angle2> <angle3> <relative speed 1 to 100>\n`
Set the angles of the 4 motors in degrees, in the range -90 to 90.

`suck\n`
Tells MCU to set the suck pin to 1

`unsuck\n`
Tells MCU to set the suck pin to 0

`req_status\n`
Signal that tells MCU to send back data on the motor (see my_status)


# MCU => PC
All of these functions are void functions

`my_status <angle0> <angle1> <angle2> <angle3> <are motors moving? (True/False)> <suction status (True/False)> <time (ms)>\n`
sends status of hopefully everything to pc

`error <message>\n`
sends error message to pc

`info <message>\n`
