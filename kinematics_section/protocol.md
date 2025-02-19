# Commands

# PC => MCU

`set_angles <angle0> <angle1> <angle2> <angle3> <rel. speed0> <rel. speed1> <rel. speed2> <rel. speed3>\n`
Set the angles of the 4 motors in degrees (decimal), in the range -90 to 90.
Set the relative speed from 0 to 1 (decimal)

`suck\n`

`unsuck\n`

`req_status\n`

`req_periodic_status <period in seconds>\n`
Request status to be sent periodically. Disable if period is 0.


# MCU => PC

`my_status <angle0> <angle1> <angle2> <angle3> <are motors moving? (True/False)> <suction status (True/False)> <time (ms)>\n`

`error <message>\n`

`info <message>\n`
