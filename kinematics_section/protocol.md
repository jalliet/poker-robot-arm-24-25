# Commands

# PC => MCU

`set_angles <angle0> <angle1> <angle2> <angle3> <relative speed 1 to 100>\n`
Set the angles of the 4 motors in degrees, in the range -90 to 90.

`suck\n`

`unsuck\n`

`req_status\n`

# MCU => PC

`my_status <angle0> <angle1> <angle2> <angle3> <are motors moving? (True/False)> <suction status (True/False)> <time (ms)>\n`

`error <message>\n`

`info <message>\n`
