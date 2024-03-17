import unittest
import math


# define Parameters
Phase = 3
ElectricalTurnsMultiplier = 2
NumberOfCoils = 2 * Phase * ElectricalTurnsMultiplier

# PCB parameters
OuterRadius = 20
InnerRadius = 10
Clearance = 0.2
TrackWidth = 0.7

# PCB content
pcb_content = []


# Clearance between the two track middle points
def calculateTrackClearance():
    return Clearance + TrackWidth


class Point:
    def __init__(self, x = 0, y = 0):
        self.X = x
        self.Y = y
        self.calcCartesian2Polar()

    def calcPolar2Cartesian(self, alfa, radius):
        self.Alfa = alfa
        self.Radius = radius
        self.X = radius * math.cos(alfa)
        self.Y = radius * math.sin(alfa)

    def calcCartesian2Polar(self):
        if self.X == 0:
            if self.Y > 0:
                self.Alfa = math.pi / 2
            else:
                self.Alfa = 3* math.pi / 2
        else:
            self.Alfa = math.atan(self.Y / self.X)

        self.Radius = math.sqrt(self.X**2 + self.Y**2)

    def distanceFromPoint(self, point):
        return math.sqrt((self.X - point.X)**2 + (self.Y - point.Y)**2)

    def distanceFromLine(self, line):
        num = abs(line.General_A * self.X + line.General_B * self.Y + line.General_C)
        div = math.sqrt(line.General_A**2 + line.General_B**2)
        return num / div

    def distanceFromLine2(self, line):
        rectangular_line = Line(line.M, line.C)
        if line.M == 0:
            return self.Y - line.C
        else:
            rectangular_line.M = - 1 / (math.atan(line.M)) #M angle ok
            rectangular_line.calculateOffset(self) #Line equation okay
            return self.distanceFromPoint(line.twoLineCross(rectangular_line))

    def changeRadius(self, radius):
        self.Radius = radius
        self.calcPolar2Cartesian(self.Alfa, self.Radius)

    def changeAlfa(self, alfa):
        self.Alfa = alfa
        self.calcPolar2Cartesian(self.Alfa, self.Radius)

    def changeX(self, x):
        self.X = x
        self.calcCartesian2Polar()

    def changeY(self, y):
        self.Y = y
        self.calcCartesian2Polar()


class Circle:
    def __init__(self,radius, start_p = Point(0,0), mid_p = Point(0,0), end_p = Point(0,0)):
        self.Radius = radius
        self.StartPoint = start_p
        self.MidPoint = mid_p
        self.EndPoint = end_p

    def crossWithLine(self, line):
        A = line.General_A * line.General_C
        D = self.Radius ** 2 * (line.General_A ** 2 + line.General_B ** 2) - line.General_C ** 2
        Div = line.General_A ** 2 + line.General_B ** 2
        B = line.General_B
        if D < 0:
            print("No solution where circle cross the line")
        else:
            x = ( A + B * math.sqrt(D) ) / Div
            y = line.M * x + line.C

            self.StartPoint = Point(x, y)
            line.EndPoint = self.StartPoint


    #add end and mid points based on the end point argument and the already given start point
    def addMidEndPoints(self, end_point):
        self.EndPoint = end_point
        tmp_point = Point()
        angle = ( self.EndPoint.Alfa + self.StartPoint.Alfa ) / 2
        tmp_point.calcPolar2Cartesian(angle, self.Radius)
        self.MidPoint = tmp_point


    def write(self, t):
        pcb_content.append(
            "(gr_arc (start " + str(self.StartPoint.X) + " " + str(self.StartPoint.Y) +") (mid " + str(self.MidPoint.X) + " " + str(self.MidPoint.Y) +") (end " + str(self.EndPoint.X) + " " + str(self.EndPoint.Y) +")\n (stroke (width " + str(TrackWidth) + ") (type default)) (layer \"F.Cu\")"+ t.addTimeStamp() +" )\n"
        )



# Create line on which the points of the coil can be
class Line:
    def __init__(self, m_angle, c_offset, start_p = Point(0,0), end_p = Point(0,0)):
        # line form y = mx + c
        self.M = m_angle
        self.C = c_offset
        self.StartPoint = start_p
        if not self.isPointonLine(start_p):
            self.movePoint2LineAlongY(start_p) # along the y axis move the point to the line to get a correct value
        self.StartPoint = start_p

        if not self.isPointonLine(end_p):
            self.movePoint2LineAlongY(end_p) # along the y axis move the point to the line to get a correct value
        self.EndPoint = end_p

        self.updateGeneralForm()

    def isPointonLine(self, point):
        # line form y = mx + c
        return point.Y == self.M * point.X + self.C

    def movePoint2LineAlongY(self, point):
        point.Y = self.M * point.X + self.C

    def updateGeneralForm(self):
        #general_m form ax + by -c = 0
        self.General_A = - self.M
        self.General_B = 1
        self.General_C = - self.C

    def crossWithCircle(self, circle):
        A = self.General_A * self.General_C
        D = circle.Radius ** 2 * (self.General_A ** 2 + self.General_B ** 2) - self.General_C ** 2
        Div = self.General_A ** 2 + self.General_B ** 2
        B = self.General_B
        if D < 0:
            print("No solution where circle cross the line")
        else:
            x = (A + B * math.sqrt(D)) / Div
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

    def write(self, t):
        pcb_content.append(
            "(segment (start " + str(self.StartPoint.X) + " " + str(self.StartPoint.Y) + ") (end " + str(self.EndPoint.X) + " " + str(self.EndPoint.Y) + ") (width " + str(TrackWidth) + ") (layer \"F.Cu\") (net 1) " + t.addTimeStamp() + ")\n"
        )


class Coil:
    def __init__(self, direction, phase, angle):
        self.Objects = []
        self.SmallCircle = []
        self.BigCircle = []
        self.RightLine = []
        self.LeftLine = []
        self.PhaseAndDirection = direction+phase
        self.InnerRadius = InnerRadius
        self.OuterRadius = OuterRadius
        self.AngleForCoil = angle
        self.SpaceForSmallCircle = True #TBC TODO
        self.LastAdded = 0 # 1: RightLine; 2: SmallCircle; 3: LeftLine; 4: BigCircle
        self.flagOneStopCriteriaMet = 0 # help decide when to stop

        self.firstRoundCoil()

    def firstRoundCoil(self):
        right_line = Line(0,0)
        right_line.paralelShiftLine(calculateTrackClearance()/2)
        self.firstObjectAppend(right_line)

        small_circle = Circle(self.InnerRadius)
        self.appendCircle(False, small_circle)

        left_line = Line(math.tan(self.AngleForCoil), 0)
        left_line.paralelShiftLine(calculateTrackClearance()/2)
        self.appendLine(False, left_line)

        big_circle = Circle(self.OuterRadius)
        self.appendCircle(True, big_circle)

    def firstObjectAppend(self, right_line):
        tmp_circle = Circle(self.OuterRadius)
        right_line.crossWithCircle(tmp_circle)
        self.RightLine.append(right_line)
        self.Objects.append(right_line)
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
        if len(self.Objects) < 4:
            return True
        else:
            tmp_circle = Circle(self.SmallCircle[-1].Radius + calculateTrackClearance()) #Next small circle
            # Check if there is place from the previous --BIG-- circle
            if tmp_circle.Radius < self.BigCircle[-1].Radius - calculateTrackClearance():
                #Make temporary copy of the last --RIGHT-- line, which is closest to the middle
                tmp_line = self.RightLine[-1]
                # Check if there is place from the previous --LEFT-- line
                tmp_circle.crossWithLine(tmp_line)
                if tmp_circle.StartPoint.distanceFromLine(self.LeftLine[-1]) > calculateTrackClearance(): # Possible circle start point distance from the previous left line
                    self.SpaceForSmallCircle = True
                    return True
                else:
                    self.SpaceForSmallCircle = False #TBC TODO
                    return False


    def checkSpaceForNextBigCircle(self):
        if len(self.Objects) < 4:
            return True
        else:
            tmp_circle = Circle(self.BigCircle[-1].Radius - calculateTrackClearance()) #Next big circle
            #Check if there is place from the previous --SMALL-- circle
            if tmp_circle.Radius > self.SmallCircle[-1].Radius + calculateTrackClearance():
                tmp_line = self.LeftLine[-1]

                tmp_circle.crossWithLine(tmp_line)
                if tmp_circle.StartPoint.distanceFromLine(self.RightLine[-1]) > calculateTrackClearance():
                    return True
                else:
                    return False

    def checkSpaceForNextRightLine(self):
        if len(self.Objects) < 4:
            return True
        else:

            tmp_circle = Circle(self.SmallCircle[-1].Radius + calculateTrackClearance())

            if tmp_circle.Radius + calculateTrackClearance() < self.BigCircle[-1].Radius:
                return True
            else:
                return False


    def checkSpaceForNextLeftLine(self):
        if len(self.Objects) < 4:
            return True
        else:
            tmp_circle = Circle(self.BigCircle[-1].Radius - calculateTrackClearance())

            if tmp_circle.Radius - calculateTrackClearance() > self.SmallCircle[-1].Radius:
                return True
            else:
                return False

    # incoming circle need only radius
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

    #check if the build-up of the coil is ongoing / is there space to continue the coil?
    def ongoingCoilBuildUp(self):
        if self.LastAdded == 1:     # RightLine
            if self.checkSpaceForNextSmallCircle():
                self.flagOneStopCriteriaMet = 0
                return True
            else:
                if self.flagOneStopCriteriaMet == 0:
                    self.flagOneStopCriteriaMet = 1
                    return True
                elif self.flagOneStopCriteriaMet == 1:
                    return False
                else:
                    print("Error at ongoingCoilBuildUp in class: Coil\nStopping criteria error in --RightLine-- branch")
                    return False

        elif self.LastAdded == 2:     # SmallCircle
            if self.checkSpaceForNextLeftLine():
                self.flagOneStopCriteriaMet = 0
                return True
            else:
                if self.flagOneStopCriteriaMet == 0:
                    self.flagOneStopCriteriaMet = 1
                    return True
                elif self.flagOneStopCriteriaMet == 1:
                    return False
                else:
                    print("Error at ongoingCoilBuildUp in class: Coil\nStopping criteria error in --SmallCircle-- branch")
                    return False


        elif self.LastAdded == 3:    # 3: LeftLine
            if self.checkSpaceForNextBigCircle():
                self.flagOneStopCriteriaMet = 0
                return True
            else:
                if self.flagOneStopCriteriaMet == 0:
                    self.flagOneStopCriteriaMet = 1
                    return True
                elif self.flagOneStopCriteriaMet == 1:
                    return False
                else:
                    print("Error at ongoingCoilBuildUp in class: Coil\nStopping criteria error in --LeftLine-- branch")
                    return False

        elif self.LastAdded == 4:    # 4: BigCircle
            if self.checkSpaceForNextRightLine():
                self.flagOneStopCriteriaMet = 0
                return True
            else:
                if self.flagOneStopCriteriaMet == 0:
                    self.flagOneStopCriteriaMet = 1
                    return True
                elif self.flagOneStopCriteriaMet == 1:
                    return False
                else:
                    print("Error at ongoingCoilBuildUp in class: Coil\nStopping criteria error in --BigCircle-- branch")
                    return False

    #Add next object
    def addNextObject(self):
        if self.LastAdded == 1:  # RightLine
            if self.checkSpaceForNextSmallCircle():
                # append Small Circle
                if len(self.SmallCircle) > 0:
                    #not the first small circle
                    self.appendCircle(False, Circle(self.SmallCircle[-1].Radius))
                else:
                    # First small Circle element
                    self.appendCircle(False, Circle(self.InnerRadius))


        elif self.LastAdded == 2:  # SmallCircle
            if self.checkSpaceForNextLeftLine():
                # append Left Line
                if len(self.LeftLine) > 0:
                    #not the first small circle
                    next_line = Line(self.LeftLine[-1].M, self.LeftLine[-1].C) #Copy previous line
                    next_line.paralelShiftLine(-calculateTrackClearance()) # shift with clearance
                    self.appendLine(False, next_line)
                else:
                    # First small Circle element
                    next_line = Line(math.tan(self.AngleForCoil), 0)
                    next_line.paralelShiftLine(-calculateTrackClearance() / 2)  # shift with clearance from other coil
                    self.appendLine(False, next_line)



        elif self.LastAdded == 3:  # 3: LeftLine
            if self.checkSpaceForNextBigCircle():
                # append Big Circle
                if len(self.BigCircle) > 0:
                    # not the first small circle
                    self.appendCircle(True, Circle(self.BigCircle[-1].Radius))
                else:
                    # First small Circle element
                    self.appendCircle(True, Circle(self.OuterRadius))


        elif self.LastAdded == 4:  # 4: BigCircle
            if self.checkSpaceForNextRightLine():
                # append Left Line
                if len(self.RightLine) > 0:
                    # not the first small circle
                    next_line = Line(self.RightLine[-1].M, self.RightLine[-1].C)  # Copy previous line
                    next_line.paralelShiftLine(calculateTrackClearance())  # shift with clearance
                    self.appendLine(True, next_line)
                else:
                    # First small Circle element
                    next_line = Line(math.tan(self.AngleForCoil), 0)
                    next_line.paralelShiftLine(calculateTrackClearance() / 2)  # shift with clearance from other coil
                    self.appendLine(True, next_line)

    def writeCoil(self, t):
        for object in self.Objects:
            object.write(t)

    def _testWriteFirstObject(self, t, number_of_element):
        for i in range(number_of_element):
            self.Objects[i].write(t)

class PCB_Motor:
    def __init__(self, Phase, NumberOfCoils):
        self.Phase = Phase
        self.NumberOfCoils = NumberOfCoils
        self.ElectricalMultiplicator = NumberOfCoils / 2 / Phase
        self.AnglePerCoil = 2 * math.pi / NumberOfCoils
        self.Coils = []

        self.firstCoil()

    #def appendCoil(self, Coil):
    #    self.Coils.append(Coil)

    def appendCoil(self, Direction, PhaseName):
        self.Coils.append(Coil(Direction, PhaseName, self.AnglePerCoil))

    def firstCoil(self):
        self.appendCoil("+", "A")

    def buildLastAddedCoil(self):
        while self.Coils[-1].ongoingCoilBuildUp():
            self.Coils[-1].addNextObject()


class time:
    def __init__(self):
        self.stamp = 79519946

    def addTimeStamp(self):
        self.stamp += 6

        return "(tstamp 8b7d6d07-02bf-4b76-bfa2-6080"+ str(self.stamp)+")"

def fileKicadSetup():
    pcb_content.append("(kicad_pcb (version 20221018) (generator pcbnew)\n ")
    pcb_content.append(" (general")
    pcb_content.append("    (thickness 1.6)")
    pcb_content.append(")\n")
    pcb_content.append("  (paper \"A4\")\n"
                       "  (layers\n"
                       "    (0 \"F.Cu\" signal)\n"
                       "    (31 \"B.Cu\" signal)\n"
                       "    (32 \"B.Adhes\" user \"B.Adhesive\")\n"
                       "    (33 \"F.Adhes\" user \"F.Adhesive\")\n"
                       "    (34 \"B.Paste\" user)\n"
                       "    (35 \"F.Paste\" user)\n"
                       "    (36 \"B.SilkS\" user \"B.Silkscreen\")\n"
                       "    (37 \"F.SilkS\" user \"F.Silkscreen\")\n"
                       "    (38 \"B.Mask\" user)\n"
                       "    (39 \"F.Mask\" user)\n"
                       "    (40 \"Dwgs.User\" user \"User.Drawings\")\n"
                       "    (41 \"Cmts.User\" user \"User.Comments\")\n"
                       "    (42 \"Eco1.User\" user \"User.Eco1\")\n"
                       "    (43 \"Eco2.User\" user \"User.Eco2\")\n"
                       "    (44 \"Edge.Cuts\" user)\n"
                       "    (45 \"Margin\" user)\n"
                       "    (46 \"B.CrtYd\" user \"B.Courtyard\")\n"
                       "    (47 \"F.CrtYd\" user \"F.Courtyard\")\n"
                       "    (48 \"B.Fab\" user)\n"
                       "    (49 \"F.Fab\" user)\n"
                       "    (50 \"User.1\" user)\n"
                       "    (51 \"User.2\" user)\n"
                       "    (52 \"User.3\" user)\n"
                       "    (53 \"User.4\" user)\n"
                       "    (54 \"User.5\" user)\n"
                       "    (55 \"User.6\" user)\n"
                       "    (56 \"User.7\" user)\n"
                       "    (57 \"User.8\" user)\n"
                       "    (58 \"User.9\" user)\n"
                       "  )\n\n"
                       "(setup\n"
                       "    (pad_to_mask_clearance 0)\n"
                       "    (pcbplotparams\n"
                       "      (layerselection 0x00010fc_ffffffff)\n"
                       "      (plot_on_all_layers_selection 0x0000000_00000000)\n"
                       "      (disableapertmacros false)\n"
                       "      (usegerberextensions false)\n"
                       "      (usegerberattributes true)\n"
                       "      (usegerberadvancedattributes true)\n"
                       "      (creategerberjobfile true)\n"
                       "      (dashed_line_dash_ratio 12.000000)\n"
                       "      (dashed_line_gap_ratio 3.000000)\n"
                       "      (svgprecision 4)\n"
                       "      (plotframeref false)\n"
                       "      (viasonmask false)\n"
                       "      (mode 1)\n"
                       "      (useauxorigin false)\n"
                       "      (hpglpennumber 1)\n"
                       "      (hpglpenspeed 20)\n"
                       "      (hpglpendiameter 15.000000)\n"
                       "      (dxfpolygonmode true)\n"
                       "      (dxfimperialunits true)\n"
                       "      (dxfusepcbnewfont true)\n"
                       "      (psnegative false)\n"
                       "      (psa4output false)\n"
                       "      (plotreference true)\n"
                       "      (plotvalue true)\n"
                       "      (plotinvisibletext false)\n"
                       "      (sketchpadsonfab false)\n"
                       "      (subtractmaskfromsilk false)\n"
                       "      (outputformat 1)\n"
                       "      (mirror false)\n"
                       "      (drillshape 1)\n"
                       "      (scaleselection 1)\n"
                       "      (outputdirectory \"\")\n"
                       "    )\n"
                       "  )\n"
                       "  (net 0 \"\")\n"
                       "  (net 1 \"3V3\")\n\n")

Motor = PCB_Motor(3, 6)
Times = time()
fileKicadSetup()
Motor.buildLastAddedCoil()
#Motor.Coils[0].writeCoil(Times)
Motor.Coils[0]._testWriteFirstObject(Times, 2)
# Join all elements of pcb_content with newline characters and print
print("\n".join(pcb_content))

class TestPoint(unittest.TestCase):
    def test_initialization(self):
        point = Point(3, 4)
        self.assertEqual(point.X, 3)
        self.assertEqual(point.Y, 4)
        self.assertAlmostEqual(point.Radius, 5)  # 3-4-5 triangle
        self.assertAlmostEqual(point.Alfa, math.atan2(4, 3))

    def test_calcPolar2Cartesian(self):
        point = Point()
        point.calcPolar2Cartesian(math.pi / 4, math.sqrt(2))
        self.assertAlmostEqual(point.X, 1)
        self.assertAlmostEqual(point.Y, 1)

    def test_calcCartesian2Polar(self):
        point = Point(1, 1)
        point.calcCartesian2Polar()
        self.assertAlmostEqual(point.Radius, math.sqrt(2))
        self.assertAlmostEqual(point.Alfa, math.pi / 4)

    def test_distanceFromPoint(self):
        point1 = Point(0, 0)
        point2 = Point(3, 4)
        self.assertAlmostEqual(point1.distanceFromPoint(point2), 5)  # 3-4-5 triangle

    def test_distanceFromLine(self):
        point = Point(5, 6)
        line = Line(1, 2, Point(0,2), Point(1,3))  # y = x + 2
        self.assertAlmostEqual(point.distanceFromLine(line), math.sqrt(2)/2, places=2)  # Should calculate perpendicular distance

    def test_changeRadius(self):
        point = Point(1, 1)
        point.changeRadius(5)
        self.assertAlmostEqual(point.Radius, 5)
        self.assertAlmostEqual(point.X, 5 / math.sqrt(2))
        self.assertAlmostEqual(point.Y, 5 / math.sqrt(2))

    def test_changeAlfa(self):
        point = Point(1, 0)
        point.changeAlfa(math.pi / 2)
        self.assertAlmostEqual(point.X, 0)
        self.assertAlmostEqual(point.Y, 1)

    def test_changeX(self):
        point = Point(0, 1)
        point.changeX(1)
        self.assertEqual(point.X, 1)
        self.assertAlmostEqual(point.Alfa, math.pi / 4)

    def test_changeY(self):
        point = Point(1, 0)
        point.changeY(1)
        self.assertEqual(point.Y, 1)
        self.assertAlmostEqual(point.Alfa, math.pi / 4)


class TestCircle(unittest.TestCase):
    def setUp(self):
        self.radius = 5
        self.circle = Circle(self.radius)

    def test_initialization(self):
        self.assertEqual(self.circle.Radius, 5)
        self.assertEqual(self.circle.StartPoint.X, 0)
        self.assertEqual(self.circle.StartPoint.Y, 0)

    def test_crossWithLine_no_intersection(self):
        # Line with no intersection with circle
        line = Line(1, 1)  # Assuming Line's constructor can handle these params
        line.General_A = 1
        line.General_B = -1
        line.General_C = 10
        self.circle.crossWithLine(line)
        # Since no actual change to circle's start point in case of no intersection, check if it remains unchanged
        self.assertEqual(self.circle.StartPoint.X, 0)
        self.assertEqual(self.circle.StartPoint.Y, 0)

    def test_crossWithLine_with_intersection(self):
        # Assuming Line's attributes are set in a way that allows for intersection
        line = Line(0, 0)
        line.General_A = 0
        line.General_B = 1
        line.General_C = -self.radius / math.sqrt(2)  # This should intersect the circle
        line.M = 0
        line.C = self.radius / math.sqrt(2)
        self.circle.crossWithLine(line)
        # Check if start point is updated to an intersection point
        self.assertAlmostEqual(self.circle.StartPoint.X, self.radius / math.sqrt(2), places=2)
        self.assertAlmostEqual(self.circle.StartPoint.Y, self.radius / math.sqrt(2), places=2)

    def test_addMidEndPoints(self):
        end_point = Point(5, 0)
        self.circle.StartPoint = Point(0, -5)  # Set start point opposite to end point
        self.circle.addMidEndPoints(end_point)
        self.assertEqual(self.circle.EndPoint, end_point)
        # Check if mid point is approximately at the circle's top, given the start and end points
        self.assertAlmostEqual(self.circle.MidPoint.X, -5 / math.sqrt(2), places=2)
        self.assertAlmostEqual(self.circle.MidPoint.Y, 5 / math.sqrt(2), places=2)


class TestLine(unittest.TestCase):
    def setUp(self):
        # Setup common test variables
        self.m_angle = 1
        self.c_offset = 0
        self.start_point = Point(0, 0)
        self.end_point = Point(1, 1)
        self.line = Line(self.m_angle, self.c_offset, self.start_point, self.end_point)

    def test_line_initialization(self):
        self.assertEqual(self.line.M, self.m_angle)
        self.assertEqual(self.line.C, self.c_offset)
        self.assertEqual(self.line.StartPoint, self.start_point)
        self.assertEqual(self.line.EndPoint, self.end_point)
        # Check general form update
        self.assertEqual(self.line.General_A, -self.m_angle)
        self.assertEqual(self.line.General_B, 1)
        self.assertEqual(self.line.General_C, -self.c_offset)

    def test_is_point_on_line(self):
        on_line_point = Point(1, 1)
        off_line_point = Point(1, 2)
        self.assertTrue(self.line.isPointonLine(on_line_point))
        self.assertFalse(self.line.isPointonLine(off_line_point))

    def test_move_point_to_line_along_y(self):
        point = Point(1, 2)  # Not on the line y = x
        self.line.movePoint2LineAlongY(point)
        self.assertTrue(self.line.isPointonLine(point))

    def test_calculate_offset(self):
        point_included = Point(2, 2)
        self.line.calculateOffset(point_included)
        self.assertEqual(self.line.C, point_included.Y - self.line.M * point_included.X)

    def test_two_line_cross(self):
        line1 = Line(1, 0)
        line2 = Line(-1, 0)
        cross_point = line1.twoLineCross(line2)
        self.assertEqual(cross_point.X, 0)
        self.assertEqual(cross_point.Y, 0)

    def test_parallel_shift_line(self):
        original_c = self.line.C
        shift = 2
        self.line.paralelShiftLine(shift)
        # Depending on how parallel shift is implemented, adjust this test
        expected_c_shifted = original_c + shift / math.cos(math.atan(self.line.M))
        self.assertAlmostEqual(self.line.C, expected_c_shifted)

    # Additional tests for `crossWithCircle` and `write` methods might require mocking or setting up more complex scenarios.




