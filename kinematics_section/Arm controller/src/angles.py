import math

ARM_REACH = 22         # This is the approximate extended arm length in centimetres
L_1 = 10               # The approximate length of the first bone of the arm, closest to the base
L_2 = 9.211            # The approximate length of the second bone of the arm, between the second and third joints
L_3 = 6.789            # The approximate length of the hand of the arm, furthest from the base
ARM_ELEVATION = 6.1    # This is the approximate height of the arm's origin above the table
ANGLE_RANGES = {0: (-180, 180), 1: (-90, 90), 2: (-160, 160), 3: (-160, 160)}
# Ranges are inclusive on the right and exclusive on the left

# positive x is the forward direction of the arm towards the cards
# postive y is the to the left when looking towards the cards
# positive z is the upwards direction
# We define the point (0, 0, 0) to be at the height of the arm base, in the centre or the arm's base
# Note that this is unreachable in reality

# positive angles are anti-clockwise
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# angle 0 for the servo at the arm's origin points to positive x 
# angle 0 for the servo at the first joint is completely relaxed
# angle 0 for the servo at the second joint is completely relaxed
# angle 0 for the servo at the third joint is completely relaxed

# The units are degrees

# The input is desired the 3D cartesian coordinates of the white arm's tip (not including the suction pin)

def validate(angles: list[float], ranges: dict) -> list[float] | ValueError:
    for i, angle in enumerate(angles):
        if angle <= ranges[i][0] or angle > ranges[i][1]:
            return ValueError(f"The arm cannot reach those coordinates due to limits in the servo angles\n The required angles are: {angles}")
    return angles

r"""
To implement this, we are going to neglect the use of z since it is taken care
of by the suction cup.

Step 1: Calculate θ and r from the x, y position using the polar coordinates
    convention. The theta value is then set for angles[0]
Step 2: Calculate angles[1] and (180-angles[2]) such that the effective radius of
    the arm is equal to r. We have a triangle defined with three side lengths
    given: r, L_1 and L_2. We can use the cosine rule twice
Step 3: Calculate angles[3] = - angles[2] - angles[3]

In the diagram below, /\ is the robot arm and ... are guidelines used to define
the angles and the triangle. In this case, angles[2] is negative and angles[1]
and angles[3] are positive.

        .
       .
      . 2
     / \
 L1 /   \ L2
   /     \
../.1.....\____  L3
      r    . 3
            .
             .


"""

def calculate_table_angles(x: float, y: float) -> list[float]:
    angles = [None, None, None, None]
    if x**2 + y**2 <= ARM_REACH**2:
        # Step 1
        if x == 0:
            angles[0] = 90
        else:
            angle0 = math.atan(y/x)
            if angle0 < 0:
                angle0 = math.pi + angle0
            angles[0] = angle0 * 180/math.pi
        radius = math.sqrt(x*x + y*y)
        if radius-L_3 <= 0:
            raise ValueError("The arm cannot reach this point because the hand is too long")
        # Step 2
        angle1 = math.acos((L_1*L_1 + (radius - L_3)*(radius - L_3) - L_2*L_2)/(2*L_1*(radius - L_3)))
        if angle1 < 0:
            angle1 = math.pi + angle1
        angles[1] = angle1 * 180/math.pi

        angle2 = math.acos((L_1*L_1 + L_2*L_2 - (radius - L_3)*(radius - L_3))/(2*L_1*L_2))
        if angle2 < 0:
            angle2 = math.pi + angle2
        angles[2] = (angle2 * 180/math.pi) - 180
        # Step 3
        angle3 = (- angles[1] - angles[2])%360
        if angle3 < 0:
            angle3 = 180 + angle3
        if angle3 > 180:
            angle3 = angle3 - 180
        angles[3] = angle3
        return validate(angles, ANGLE_RANGES)
    else:
        raise ValueError("The arm cannot reach those coordinates because it is outside the maximum reach of the arm")
    
    
if __name__ == "__main__":
    print(calculate_table_angles(20,3))