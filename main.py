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

# PCB content
pcb_content = []


# Clearance between the two track middle points
def calculateTrackClearance():
    return Clearance + TrackWidth


class Point:
    def __init__(self, x = 0, y = 0):
        self.X = x
        self.Y = y
        if x == 0:
            self.Alfa = math.pi / 2
        else:
            self.Alfa = math.atan(y / x)

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


    def write(self):
        pcb_content.append(
            "(gr_arc (start " + self.StartPoint.X + " " + self.StartPoint.Y +") (mid " + self.MidPoint.X + " " + self.MidPoint.Y +") (end " + self.EndPoint.X + " " + self.EndPoint.Y +")\n (stroke (width " + TrackWidth + ") (type default)) (layer \"F.Cu\") )\n"
        )



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

    def write(self):
        pcb_content.append(
            "(segment (start " + self.StartPoint.X + " " + self.StartPoint.Y + ") (end " + self.EndPoint.X + " " + self.EndPoint.Y + ") (width " + TrackWidth + ") (layer \"F.Cu\") (net 1) )\n"
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

        self.firstObjectAppend(Circle(self.OuterRadius))

    def firstObjectAppend(self, right_line):
        right_line.StartPoint = Point(self.OuterRadius,0)
        self.RightLine.append(right_line)
        self.Objects.append(right_line)
        self.LastAdded = 4

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
                if tmp_circle.StartPoint.distanceFromLine(self.LeftLine[-1]) > calculateTrackClearance():# Possible circle start point distance from the previous left line
                    self.SpaceForSmallCircle = True
                    return True
                else:
                    self.SpaceForSmallCircle = False #TBC TODO
                    return False


    def checkSpaceForNextBigCircle(self): #TODO
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

    def checkSpaceForNextRightLine(self):  # TODO
        if len(self.Objects) < 4:
            return True
        else:

            tmp_circle = Circle(self.SmallCircle[-1].Radius + calculateTrackClearance())

            if tmp_circle.Radius + calculateTrackClearance() < self.BigCircle[-1].Radius:
                return True
            else:
                return False


    def checkSpaceForNextLeftLine(self): #TODO
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
                    self.appendCircle(False, Circle(self.SmallCircle[-1]))
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
                    self.appendCircle(True, Circle(self.BigCircle[-1]))
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

    def writeCoil(self):
        for object in self.Objects:
            object.write()

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


def fileKicadSetup():
    pcb_content.append("(kicad_pcb (version 20221018) (generator pcbnew)\n  (general\n"
                       "    (thickness 1.6)\n  )\n"
                       "  (paper \"A4\")\n"
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

Motor = PCB_Motor(3, 12)
fileKicadSetup()
Motor.buildLastAddedCoil()
Motor.Coils[0].writeCoil()



# Output to a file or print to console
print(pcb_content)
