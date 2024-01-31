import math


# define Parameters
Phase = 3
ElectricalTurnsMultiplier = 2
NumberOfCoils = 2 * Phase * ElectricalTurnsMultiplier

# PCB parameters
OuterRadius = 15
InnerRadius = 5
Clearance = 0.2
TrackWidth = 0.7


# Clearance between the two track middle points
def calculateTrackClearance():
    return Clearance + TrackWidth


class Point:
    def __init__(self, x = 0, y = 0):
        self.X = x
        self.Y = y
        self.Alfa = math.atan( y / x)
        self.Radius = math.sqrt(x^2 + y^2)

    def calcCartesian2Polar(self, alfa, radius):
        self.Alfa = alfa
        self.Radius = radius
        self.X = radius * math.cos(alfa)
        self.Y = radius * math.sin(alfa)

    def distanceFromPoint(self, point):
        return (self.X - point.X)^2 + (self.Y - point.Y)^2


    def distanceFromLine(self, line):
        rectangular_line = line
        rectangular_line.M = - 1 / (math.atan(line.M)) #M angle ok
        rectangular_line.calculateOffset(self) #Line equation okay
        return self.distanceFromPoint(line.twoLineCross(rectangular_line))




class Circle:
    def __init__(self,radius, start_p = Point(0,0), mid_p = Point(0,0), end_p = Point(0,0)):
        self.Radius = radius
        self.StartPoint = start_p
        self.MidPoint = mid_p
        self.EndPoint = end_p

    def crossWithLine(self, line):
        A = line.M^2 + 1
        B = 2 * line.M * line.C
        C = line.C ^ 2 + self.Radius
        if (B ^ 2 - 4 * A * C < 0):
            print("No solution where circle cross the line")
        else:
            x = (-B + math.sqrt(B ^ 2 - 4 * A * C)) / (2 * A)
            y = line.M * x + line.C

            self.StartPoint = Point(x, y)
            line.EndPoint = self.StartPoint


    #add end and mid points based on the end point argument and the already given start point
    def addMidEndPoints(self, end_point):
        self.EndPoint = end_point
        tmp_point = Point()
        angle = ( self.EndPoint.Alfa + self.StartPoint.Alfa ) / 2
        tmp_point.calcCartesian2Polar(angle, self.Radius)



# Create line on which the points of the coil can be
class Line:
    def __init__(self, m_angle, c_offset, start_p = Point(0,0), end_p = Point(0,0)):
        self.M = m_angle
        self.C = c_offset
        self.StartPoint = start_p
        self.EndPoint = end_p

    def crossWithCircle(self, circle):
        A = self.M ^ 2 + 1
        B = 2 * self.M * self.C
        C = self.C ^ 2 + circle.Radius ^ 2

        if B ^ 2 - 4 * A * C < 0:
            print("No solution where circle cross the line")
        else:
            x = (-B + math.sqrt(B ^ 2 - 4 * A * C)) / (2 * A)
            y = self.M * x + self.C
            self.StartPoint = Point(x, y)
            circle.addMidEndPoints(self.StartPoint)

    def calculateOffset(self, point_included):
        self.C = point_included.Y - self.M * point_included.X

    def twoLineCross(self, line):
        #line equation = 0 = m1*x - -1*y + c1
        x = (-line.C + self.C) / ( line.M - self.M)
        y = (self.C*line.M - self.M*line.C) / (line.M-self.M)
        return Point(x,y)

    # paralel shift viewpoint of the y axis
    # positive shift results in a bigger
    def paralelShiftLine(self, shift):
        self.C = self.C + shift / math.cos(math.atan(self.M))


class Coil:
    def __init__(self, direction, phase):
        self.Objects = []
        self.SmallCircle = []
        self.BigCircle = []
        self.RightLine = []
        self.LeftLine = []
        self.PhaseAndDirection = direction+phase
        self.InnerRadius = InnerRadius
        self.OuterRadius = OuterRadius
        self.SpaceForSmallCircle = True #TBC TODO
        self.LastAdded = 0 # 1: RightLine; 2: SmallCircle; 3: LeftLine; 4: BigCircle

        self.firstObjectAppend(Circle(self.OuterRadius))

    def firstObjectAppend(self, right_line):
        right_line.StartPoint = Point(self.OuterRadius,0)
        self.RightLine[0] = right_line
        self.Objects[0] = right_line
        self.LastAdded = 1

    def appendLine(self, orientation_right, line):
        if orientation_right:
            line.crossWithCircle(self.Objects[-1])
            self.RightLine.append(line)
            self.Objects.append(line)
            self.LastAdded = 1

        else: #orientation Left
            self.LeftLine.append(line)
            self.Objects.append(line)
            self.LastAdded = 3

    def checkSpaceForNextSmallCircle(self):
        tmp_circle = Circle(self.SmallCircle[-1].Radius + calculateTrackClearance()) #Next small circle
        # Check if there is place from the previous --BIG-- circle
        if tmp_circle.Radius < self.BigCircle[-1].Radius - calculateTrackClearance():
            #Make temporary copy of the last --RIGHT-- line, which is closest to the middle
            tmp_line = self.RightLine[-1]
            # Check if there is place from the previous --LEFT-- line
            tmp_circle.crossWithLine(tmp_line)
            if tmp_circle.StartPoint.distanceFromLine(self.LeftLine[-1]) > calculateTrackClearance():# Possible circle start point distance from the previous left line
                self.SpaceForSmallCircle = True
                return True
            else:
                self.SpaceForSmallCircle = False #TBC TODO
                return False

    def checkSpaceForNextBigCircle(self): #TODO
        tmp_circle = Circle(self.BigCircle[-1].Radius - calculateTrackClearance()) #Next big circle
        #Check if there is place from the previous --SMALL-- circle
        if tmp_circle.Radius > self.SmallCircle[-1].Radius + calculateTrackClearance():
            tmp_line = self.LeftLine[-1]

            tmp_circle.crossWithLine(tmp_line)
            if tmp_circle.StartPoint.distanceFromLine(self.RightLine[-1]) > calculateTrackClearance():
                return True
            else:
                return False

    def checkSpaceForNextRightLine(self):  # TODO
        tmp_circle = Circle(self.SmallCircle[-1].Radius + calculateTrackClearance())

        if tmp_circle.Radius + calculateTrackClearance() < self.BigCircle[-1].Radius:
            return True
        else:
            return False


    def checkSpaceForNextLeftLine(self): #TODO
        tmp_circle = Circle(self.BigCircle[-1].Radius - calculateTrackClearance())

        if tmp_circle.Radius - calculateTrackClearance() > self.SmallCircle[-1].Radius:
            return True
        else:
            return False

    def appendCircle(self, size_big, circle):
        if size_big:
            circle.crossWithLine(self.Objects[-1])
            self.BigCircle.append(circle)
            self.Objects.append(circle)
            self.LastAdded = 4

        else:
            circle.crossWithLine(self.Objects[-1])
            self.SmallCircle.append(circle)
            self.Objects.append(circle)
            self.LastAdded = 2

    def ongoingCoilBuildUp(self):
        if self.LastAdded == 1:     # RightLine
            

        if self.LastAdded == 2:     # SmallCircle

        if self.LastAdded == 3:    # 3: LeftLine

        if self.LastAdded == 4:    # 4: BigCircle

class PCB_Motor:
    def __init__(self, Phase = Phase, NumberOfCoils = NumberOfCoils):
        self.Phase = Phase
        self.NumberOfCoils = NumberOfCoils
        self.ElectricalMultiplicator = NumberOfCoils / 2 / Phase
        self.Coils = []

        self.firstCoil()

    #def appendCoil(self, Coil):
    #    self.Coils.append(Coil)

    def appendCoil(self, Direction, PhaseName):
        self.Coils.append(Coil(Direction, PhaseName))

    def firstCoil(self):
        self.appendCoil("+", "A")

    def buildLastAddedCoil(self):
        self.Coils[-1].



def generate_round_coil_kicad_pcb(turns, track_width, turn_spacing):
    pcb_content = []

    # Start of the kicad_pcb file
    pcb_content.append('(kicad_pcb (version 20221018) (generator pcbnew)')
    pcb_content.append('  ...')  # Placeholder for other PCB settings

    # Start of the footprint
    pcb_content.append(f'  (footprint "ROUND_COIL_{turns}TURNS" (layer "F.Cu")')
    pcb_content.append('    (attr smd)')
    pcb_content.append('    (at 100 100)')  # Position of the coil center

    # Radius of the first turn
    radius = 5

    # Generate the turns
    for turn in range(turns):
        # Define the radius for this turn
        inner_radius = radius + turn * (track_width + turn_spacing)
        outer_radius = inner_radius + track_width

        # Draw the first half-circle
        pcb_content.append(
            f'    (fp_arc (start 100 100) (end 100 {100 + inner_radius}) (angle 180) (layer "F.Cu") (width {track_width}))')
        # Draw the second half-circle
        pcb_content.append(
            f'    (fp_arc (start 100 100) (end 100 {100 - outer_radius}) (angle -180) (layer "F.Cu") (width {track_width}))')

    # Add connection pads
    pcb_content.append(
        f'    (pad "1" smd circle (at 100 {100 - radius - 0.5 * track_width}) (size {track_width} {track_width}) (layers "F.Cu"))')
    final_outer_radius = radius + (turns - 1) * (track_width + turn_spacing) + track_width
    pcb_content.append(
        f'    (pad "2" smd circle (at 100 {100 - final_outer_radius - 0.5 * track_width}) (size {track_width} {track_width}) (layers "F.Cu"))')

    # End of the footprint
    pcb_content.append('  )')

    # End of the kicad_pcb file
    pcb_content.append(')')

    # Join all the content into a single string
    return '\n'.join(pcb_content)


# Parameters
number_of_turns = 5
track_width = 0.15
turn_spacing = 0.15

# Generate the PCB content
pcb_file_content = generate_round_coil_kicad_pcb(number_of_turns, track_width, turn_spacing)

# Output to a file or print to console
print(pcb_file_content)
