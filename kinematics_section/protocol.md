# Commands

# PC => MCU

<<<<<<< HEAD
`set_pin <pin> <(True/False)>`
Sets the desired pin to true or false

`set_angles <angle0> <angle1> <angle2> <angle3> <relative speed 1 to 100>\n`
Set the angles of the 4 motors in degrees, in the range -90 to 90.
=======
`set_angles <angle0> <angle1> <angle2> <angle3> <rel. speed0> <rel. speed1> <rel. speed2> <rel. speed3>\n`
Set the angles of the 4 motors in degrees (decimal), in the range -90 to 90.
Set the relative speed from 0 to 1 (decimal)
>>>>>>> 89a9496479849c67b3e3f5d60894e419e1ed2d59

`suck\n`
Tells MCU to set the suck pin to 1

`unsuck\n`
Tells MCU to set the suck pin to 0

`req_status\n`
Signal that tells MCU to send back data on the motor (see my_status)


`req_periodic_status <period in seconds>\n`
Request status to be sent periodically. Disable if period is 0.


# MCU => PC
All of these functions are void functions

`my_status <angle0> <angle1> <angle2> <angle3> <are motors moving? (True/False)> <suction status (True/False)> <time (ms)>\n`
sends status of hopefully everything to pc

`error <message>\n`
sends error message to pc

`info <message>\n`
