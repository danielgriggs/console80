import os
import pygame
import pygame.gfxdraw
import math
import logging
import random

# Todo
# Add cover layer
# Digital display!
# Segmented LED bar style display.
# Single LED display.
# Max history
# Multi value
# Line chart.

class MainScreen:
    screen = None;
    
    def __init__(self, hw=False):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            logging.info("I'm running under X display = {0}".format(disp_no))
        
        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            os.putenv('SDL_FBDEV', '/dev/fb0')
            os.putenv('SDL_NOMOUSE', '1')
           # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                logging.critical('Driver: {0} failed.'.format(driver))
                continue
            found = True
            break
    
        if not found:
            raise Exception('No suitable video driver found!')

        # Find the size of the screen.
        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self.size = size
        logging.info("Framebuffer size: %d x %d" % (size[0], size[1]))

        # Figure out what flags for initialisation are.
        flags = pygame.FULLSCREEN
        if hw is True:
            flags |= pygame.HWSURFACE

        # Create a surface.
        self.screen = pygame.display.set_mode(size, flags)
        # Initialise a font?
        pygame.font.init()

        # Setup basic colours and borders.
        self.screenBgColour = (0,0,0)
        self.wScreenBorderWidth = 5
        self.wScreenBgColour = (50,50,50)

        # Clear the screen to start
        self.screen.fill(self.screenBgColour)
        # Store the Working Window Size.
        self.wSize = (size[0] - (self.wScreenBorderWidth*2),
                      size[1] - (self.wScreenBorderWidth*2))
        # Generate a working screen.
        self.wScreen = self.screen.subsurface((self.wScreenBorderWidth,
                                               self.wScreenBorderWidth,
                                               self.wSize[0],
                                               self.wSize[1]))
        # Fill it with a colour!
        self.wScreen.fill(self.wScreenBgColour)

        # Render the screen
        pygame.display.update()

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def createClock(self):
        return pygame.time.Clock()

    def redrawScreen(self):
        pygame.display.flip()

    def autoLayoutPanels(self,panels=(4,3),label=0):
        "Figure out dimensions for how big the panels are and generates and array of panels."
        "Takes a simple tuple of columns by rows."

        # calculate maximum column width.
        columnSize = self.wSize[0] / float(panels[0])
        logging.debug("Column size is {} / {} = {}".format(self.wSize[0],panels[0],columnSize))
        rowSize = int ( self.wSize[1] / float(panels[1]) )
        logging.debug("Row size is {} / {} = {}".format(self.wSize[1],panels[1],rowSize))

        # We need the smaller of the two
        maxSize = columnSize
        vMaxSize = maxSize
        if columnSize > rowSize:
            maxSize = int( rowSize * ( 1.00 / (1.00 + label) ) )
            vMaxSize = rowSize

        # Shim a shim.
        maxSize -= 1
        # So size is now maxSize by maxSize, figure out offsets.
        # Also make the maxSize divisiable by two.
        halfwidth = math.floor(maxSize / 2)
        maxSize = int ( halfwidth * 2 )
        logging.debug("choosen maxSize of side is {}".format(maxSize))

        # Centre offset is the left over pixels divided by the numbers of panels + 1
        XOffSet = int( ( self.wSize[0] - (panels[0] * maxSize) ) / float( panels[0] + 1 ) ) + maxSize
        YOffSet = int( ( self.wSize[1] - (panels[1] * vMaxSize) ) / float( panels[1] + 1 ) ) + vMaxSize
        logging.debug("Offsets are X:{} Y:{}".format(XOffSet,YOffSet))

        # create an array for panels.
        panelPositions = []
        for y in xrange(panels[1],0,-1):
            for x in xrange(1,panels[0]+1,1):
                xPos = int( XOffSet * x ) - maxSize
                yPos = int( YOffSet * y ) - vMaxSize
                logging.debug("int( {} * {} ) - {} = {}".format(XOffSet,x,halfwidth,xPos))
                panelPositions.append({ "rect" : (xPos, yPos, maxSize, maxSize), "rpos" : (x, y)})
        return panelPositions

class GenericPanel():
    def __init__(self,screen,rect,label=0):
        "Ininitializes basic panel data"
        # Store a reference to the screen.
        self.screen = screen
        self.rect = rect
        # Label Settings
        self.boxLabelSize = label
        self.boxLabelText = "No Label"
        self.boxLabelTextColour = (255,255,255)
        self.boxLabelBorderWidth = 0
        self.boxLabelBorderColour = (255,255,255)
        self.boxLabelBgColour = (50,50,50)
        # Box settings
        self.boxBorderWidth = 1
        self.boxBorderColour = (255,255,255)
        self.boxBgColour = (100,100,100)
        self.boxName = "GenericPanel"
        
        # Generate a subsurface for this panel..
        self.panel = self.screen.subsurface(rect)
        
        # Generate a subsurface for the label.
        if self.boxLabelSize > 0:
            labelRect = pygame.Rect(rect[0],
                                    rect[1]+rect[3],
                                    rect[2],
                                    int ( math.floor(rect[3] * label)) - 1)
            logging.debug("Screen Size: {}".format(self.screen))
            logging.debug("Box Size: {}".format(rect))
            logging.debug("Label Size: {}".format(labelRect))
            self.panelLabel = self.screen.subsurface(labelRect)
            if self.boxLabelBorderWidth > 0:
                pygame.draw.rect(self.panelLabel,
                                 self.boxLabelBorderColour,
                                 self.panelLabel.get_rect(),
                                 self.boxLabelBorderWidth)

        self.panelSize = self.panel.get_size()
        self._draw_background()
        self._draw_label()

    def _draw_background(self):
        "Internal method for regenerating the background"
        # Fill up the background with a colour.
        self.panel.fill(self.boxBgColour)
        # Border width is centered, needs
        # border width/2 offset
        if self.boxBorderWidth > 0:
            pygame.draw.rect(self.panel,
                             self.boxBorderColour,
                             self.panel.get_rect(),
                             self.boxBorderWidth)

    def _draw_label(self):
        if self.boxLabelSize > 0:
            # Fill the label with background colour
            self.panelLabel.fill(self.boxLabelBgColour)
            # render a box with text.
            if not hasattr(self, 'labelFont'):
                boxHeight = int( math.floor( self.panelLabel.get_height() ))
                self.labelFont = pygame.font.Font('fonts/Impact Label Reversed.ttf', boxHeight)
            Text = self.labelFont.render(self.boxLabelText,
                                         1,
                                         self.boxLabelTextColour,
                                         self.boxLabelBgColour)
            # Even though this is called once it effects the
            # long term running of the code?!
            # Seems to be about 574 vs 568 speed difference
            if True:
                # Convert to display format (faster, also allows scaling)
                Text = Text.convert()
                textRect = Text.get_rect()
                # Get the Label size
                panelLabelRect = self.panelLabel.get_rect()
                # Scale it inside
                scaledSize = textRect.fit(panelLabelRect)            
                # transform and copy.
                scaledText = pygame.transform.smoothscale(Text,scaledSize.size)
                self.panelLabel.blit(scaledText,scaledSize)
            else:
                self.panelLabel.blit(Text,(0,0))
                
    def setBGColour(self,colour):
        self.boxBgColour = colour
        self._draw_background()
        
    def setBorderColour(self,colour):
        self.boxBorderColour = colour
        self._draw_background()
        
    def setBorderWidth(self,width):
        self.boxBorderWidth = width
        self._draw_background()

    def setLabelText(self,text):
        self.boxLabelText = text
        self._draw_label()        

    def setName(self,text):
        self.boxName = text
        
    def getName(self):
        return self.boxName

    def addDial(self,offsetStyle=False):
        self.dial = DialIndicator(self.panel,offsetStyle)
        self.dial._render()
        
    def addBar(self):
        self.dial = BarIndicator(self.panel)
        self.dial._render()
        
    def addScatter(self):
        self.dial = ScatterIndicator(self.panel)
        self.dial._render()
        
class GenericSingleValue(object):
    def __init__(self):
        "Create a place to store and manipulate a value"
        # Store a reference to the screen.
        self.value = 0
        self.valueHistory = []
        self.maxHistory = 5
        self.maxValue = 100
        self.minValue = 0
        
    def setValue(self,value):
        # Record current value to history
        self.valueHistory.append(self.value)
        # Record new value
        self.value = value
        # Clear history
        while len(self.valueHistory) > self.maxHistory:
            self.valueHistory.pop(0)
        self._render()

    def setRandValue(self):
        # Get the current value
        curValue = self.getValue()
        newValue = curValue + random.randint(-1, 1)
        # Record new value
        self.setValue(newValue)

    def getValue(self):
        "Return the current clipped value"
        if self.value > self.maxValue:
            return self.maxValue
        elif self.value < self.minValue:
            return self.minValue
        else:
            return self.value

    def setRange(self,Range):
        "Set the accepted input range as a tuple (low,high)"
        self.maxValue = Range[1]
        self.minValue = Range[0]
                        
    def isClipped(self):
        "Return whether the current value is clipped"
        if self.value < self.maxValue:
            if self.value > self.minValue:
                return False
        return True
        
class GenericIndicator(object):
    def __init__(self,surface):
        "Ininitializes basic panel data"
        # Store a reference to the screen.
        self.surface = surface
        # Set up the box.
        self.boxPosition = (0,0)
        self.boxSize = surface.get_size()
        self.boxBorderWidth = 2
        self.boxBorderColour = (255,255,255)
        self.boxBgColour = (0,0,0)
        # Store generic values.
        self.value = 0
        self.valueHistory = []
        self.maxHistory = 5
        self.maxValue = 100
        self.minValue = 0
        # Initialise bits and bobs.
        # self._draw_background()
        self.render_overlay = False

    def _draw_background(self):
        self.background = pygame.Surface(self.boxSize,flags=pygame.HWSURFACE)
        # print "Surface flags {:#x}".format(self.background.get_flags())
        self.background = self.background.convert_alpha()
        # print "{:#x}".format(self.background.get_flags())

    def _get_float_range(self,start,stop,step):
        r = start
        while r < stop:
            yield r
            r += step

    def setPosition(self,position):
        "Accept new position as (x,y)"
        self.boxPosition = position
        
    def renderOverlay(self,Render=None):
        "Set whether the overlay should rendered, returns current status."
        # print "Setting render overlay to {}".format(Render)
        if Render is not None:
            self.render_overlay = Render
        return self.render_overlay

    def setSize(self,size):
        "Accept new size as (x,y)"
        self.boxSize = size
        # re-initialise background size
        self._draw_background()

    def boxBorderDetails(self,Width=False,Colour=False,BgColour=False):
        if Width is not False:
            self.boxBorderWidth = int(Width)
        if Colour is not False:
            self.boxBorderColour = Colour
        if BgColour is not False:
            self.boxBgColour = BgColour
        
    def setValue(self,value):
        # Record current value to history
        self.valueHistory.append(self.value)
        # Record new value
        self.value = value
        # Clear history
        while len(self.valueHistory) > self.maxHistory:
            self.valueHistory.pop(0)
        self._render()

    def setRandValue(self):
        # Get the current value
        curValue = self.getValue()
        newValue = curValue + random.randint(-1, 1)
        # Record new value
        self.setValue(newValue)

    def getValue(self):
        "Return the current clipped value"
        if self.value > self.maxValue:
            return self.maxValue
        elif self.value < self.minValue:
            return self.minValue
        else:
            return self.value

    def setRange(self,Range):
        "Set the accepted input range as a tuple (low,high)"
        self.maxValue = Range[1]
        self.minValue = Range[0]
                        
    def isClipped(self):
        "Return whether the current value is clipped"
        if self.value < self.maxValue:
            if self.value > self.minValue:
                return False
        return True

class GenericBiIndicator(object):
    def __init__(self,surface):
        "Ininitializes basic panel data"
        # Store a reference to the screen.
        self.surface = surface
        # Set up the box.
        self.boxPosition = (0,0)
        self.boxSize = surface.get_size()
        self.boxBorderWidth = 2
        self.boxBorderColour = (255,255,255,255)
        self.boxBgColour = (0,0,0,255)
        self.render_overlay = False
        # Store co-ordinate values.
        self.value = (0,0)
        self.valueHistory = []
        self.maxHistory = 5
        # Min, Max       X  ,Y
        self.maxValue = (100,100)
        self.minValue = (0  ,0)

    def _draw_background(self):
        self.background = pygame.Surface(self.boxSize,flags=pygame.HWSURFACE)
        self.background = self.background.convert_alpha()

    def setSize(self,size):
        "Accept new size as (x,y)"
        self.boxSize = size
        # re-initialise background size
        self._draw_background()
        
    def setPosition(self,position):
        "Accept new position as (x,y)"
        self.boxPosition = position
        
    def renderOverlay(self,Render=None):
        "Set whether the overlay should rendered, returns current status."
        if Render is not None:
            self.render_overlay = Render
        return self.render_overlay

    def setValue(self,value):
        "This must be a (x,y) Tuple"
        # Should be a co-ordinate. (x,y)
        if not isinstance(value, tuple) or len(value) != 2:
            raise TypeError("This should be co-ordinates")
        
        # Record to history
        self.valueHistory.append(self.value)
        
        # Record new value
        self.value = value
        
        # Clean up the history
        while len(self.valueHistory) > self.maxHistory:
            self.valueHistory.pop(0)
        self._render()

    def setRandValue(self):
        # Get the current value
        curValue = self.getValue()
        newValueX = curValue[0] + random.randint(-1, 1)
        newValueY = curValue[1] + random.randint(-1, 1)
        # Record new value
        self.setValue((newValueX,newValueY))

    def getValue(self):
        "Return the current clipped value"
        value = ['','']
        for i in (0, 1):
            if self.value[i] > self.maxValue[i]:
                value[i] = self.maxValue[i]
            elif self.value[i] < self.minValue[i]:
                value[i] = self.minValue[i]
            else:
                value[i] = self.value[i]
                
        return value

    def isClipped(self):
        "Return whether or not the current value is clipped"
        for i in (0, 1):
            if self.value[i] > self.maxValue[i]:
                return True
            elif self.value[i] < self.minValue[i]:
                return True
        return False
        



class ScatterIndicator(GenericBiIndicator):
    "Scatter Graph for lack of a better name"
    def __init__(self,screen):
        GenericBiIndicator.__init__(self,screen)
        "Ininitializes a new scatter graph"
        # axisZero for   X,Y
        self.axisMax = (100,100)
        self.axisMin = (  0,  0)
        self.axisZero   = (50,50)
        self.axisWidth  = 1
        self.axisColour = (255,255,255)
        self.pointColour  = (0,255,0)
        self.pointColourClipped  = (255,0,0)
        self.pointRadius  = 5
        self.pointOutline = 1
        self.boxBorderWidth = 1
        
    def _draw_background(self):
        GenericBiIndicator._draw_background(self)
        # Draw outside box.
        if self.boxBorderWidth > 0:
            pygame.draw.rect(self.background, self.boxBorderColour, ((0,0),self.boxSize), self.boxBorderWidth)

        # Draw the X Axis, at the Y 
        maxYRange = self.maxValue[1] - self.minValue[1]
        normZeroOnY = self.axisZero[1] - self.minValue[1]

        logging.debug("axisZero[1] = {} self.minValue[1] = {}".format(self.axisZero[1],self.minValue[1]))
        logging.debug("boxSize[Y] {} maxYRange {} normZeroOnY {}".format(self.boxSize[0], maxYRange, normZeroOnY))
        scaledXZero = int( self.boxSize[1] * ( normZeroOnY / float(maxYRange) ) ) - 1
        logging.debug("  Draw from {},{} to {},{}".format(0                ,scaledXZero,
                                                  self.boxSize[0]-1,scaledXZero))
        pygame.draw.line(self.background,
                         self.axisColour,
                         (0                ,scaledXZero),
                         (self.boxSize[0]-1,scaledXZero),
                         self.axisWidth)

        # Draw the Y Axis, at the X
        maxXRange   = self.maxValue[0] - self.minValue[0]
        normZeroOnX = self.axisZero[0] - self.minValue[0]
        logging.debug("boxSize[X] {} maxXRange {} normZeroOnX {}".format(self.boxSize[1], maxXRange, normZeroOnX))
        scaledYZero = int( self.boxSize[0] * ( normZeroOnX / float(maxXRange) ) ) - 1
        logging.debug("  Draw from {},{} to {},{}".format(scaledYZero, 0,
                                                  scaledYZero, self.boxSize[1]-1))
        pygame.draw.line(self.background,
                         self.axisColour,
                         (scaledYZero, 0),
                         (scaledYZero, self.boxSize[1]-1),
                         self.axisWidth)
        
        # Decide how big the circle should be.
        self.pointRadius = int( math.ceil(maxXRange / 20 ))

        # Line length for sub markers.
        lineLength = int( math.ceil( self.boxSize[1] / 50 ))
        # Draw little lines along the vertical axis.
        divisionsDist = int( math.ceil( scaledYZero / 10.0 )) * 2
        for i in xrange(scaledYZero, self.boxSize[1], divisionsDist):
            pygame.gfxdraw.hline(self.background,
                                 scaledXZero - lineLength,
                                 scaledXZero + lineLength,
                                 i,
                                 self.boxBorderColour)
        for i in xrange(scaledYZero, 0, -divisionsDist):
            pygame.gfxdraw.hline(self.background,
                                 scaledXZero - lineLength,
                                 scaledXZero + lineLength,
                                 i,
                                 self.boxBorderColour)
            
        # Draw little lines along the horizontal axis.
        divisionsDist = int( math.ceil( scaledXZero / 10.0 )) * 2
        for i in xrange(scaledXZero, self.boxSize[0], divisionsDist):
            pygame.gfxdraw.vline(self.background,
                                 i,
                                 scaledYZero - lineLength,
                                 scaledYZero + lineLength,
                                 self.boxBorderColour)
        for i in xrange(scaledYZero, 0, -divisionsDist):
            pygame.gfxdraw.vline(self.background,
                                 i,
                                 scaledYZero - lineLength,
                                 scaledYZero + lineLength,
                                 self.boxBorderColour)
                    
    def _render(self):
        if not hasattr(self, 'background'):
            self._draw_background()
        panel = self.background.copy()
        value = self.getValue()
        
        maxYRange = self.maxValue[1] - self.minValue[1]
        normValueOnY = value[1] - self.minValue[1]
        scaledY = int( self.boxSize[1] * ( normValueOnY / float(maxYRange) ) )
        
        # Calculate X value
        maxXRange = self.maxValue[0] - self.minValue[0]
        normValueOnX = value[0] - self.minValue[0]
        scaledX = int( self.boxSize[0] * ( normValueOnX / float(maxXRange) ) )

        pointColour = self.pointColour
        pointOutline = self.pointOutline
        if self.isClipped() is True:
            pointColour = self.pointColourClipped
            pointOutline  = 0
            
        pygame.draw.circle(panel,
                           pointColour, # Colour
                           (scaledX,scaledY), # Circle Centre
                           self.pointRadius, # Radius
                           pointOutline) # line width Zero for fill
        tPanel = pygame.transform.flip(panel,False,True)
        self.surface.blit(tPanel,self.boxPosition)
        self._render_overlay()
        
    def _render_overlay(self):
        if self.render_overlay is False:
            return
        
        # overlay = pygame.Surface(self.boxSize,flags=pygame.HWSURFACE)
        # overlay = self.background.convert_alpha()
        # overlay.fill((0,0,0,0))

        # Figure out text size
        textSize = int( math.ceil( self.boxSize[0] / 10.0 ))
        if not hasattr(self, 'overlayFont'):
            # Create a font cache
            self.overlayFont = pygame.font.Font('fonts/destructobeambb_reg.ttf', textSize)

        curValue = self.getValue()
        # Put the text in a Var for later.
        xText = "X {:03}".format(curValue[0])
        yText = "Y {:03}".format(curValue[1])
        lineSize = self.overlayFont.get_linesize()

        if not hasattr(self, 'overlayCache'):
            self.overlayCache = dict()
            
        # Render the text, if it's not cached
        if xText in self.overlayCache:
            xLabel = self.overlayCache[xText]
        else:
            xLabel = self.overlayFont.render(xText, 1, (255,255,255))
            self.overlayCache[xText] = xLabel

        if yText in self.overlayCache:
            yLabel = self.overlayCache[yText]
        else:
            yLabel = self.overlayFont.render(yText, 1, (255,255,255))
            self.overlayCache[yText] = yLabel


        # Blit to overlay
        # overlay.blit(xLabel,(textSize,textSize))
        # overlay.blit(yLabel,(textSize,textSize + lineSize ))
        # self.surface.blit(overlay,self.boxPosition)
        
        # Try direct blit with no overlay.
        self.surface.blit(xLabel,(textSize,textSize))
        self.surface.blit(yLabel,(textSize,textSize + lineSize ))
            

        

class DigitalIndicator(GenericIndicator):
    "Digital numerical data"
    def __init__(self,screen, Solid=True, Sideways=True):
        "Ininitializes a new BarGraph"
        GenericIndicator.__init__(self,screen)
        self.digitalColour = (0,255,0)
        self.digitalColourClipped = (255, 0, 0)
        self.digitalCount = 5

    def _draw_background(self):
        GenericIndicator._draw_background(self)
        # Draw outside box.
        pygame.draw.rect(self.background,
                         self.boxBorderColour,
                         ((0,0),self.boxSize),
                         self.boxBorderWidth)
        self.barPadding = int( math.ceil ( self.boxSize[0] / 20 ))
        
        # Draw scale marks.
        if self.sideways is True:
            divisionWidth = int( math.ceil(self.boxSize[0] / 10.0 ))        
            for i in xrange(0,self.boxSize[0],divisionWidth):
                # Bottom lines
                pygame.gfxdraw.vline(self.background,
                                     i,
                                     0,
                                     int( math.floor(self.boxSize[1] / 20.0 )),
                                     self.boxBorderColour)
                # Top lines
                pygame.gfxdraw.vline(self.background,
                                     i,
                                     self.boxSize[1],
                                     self.boxSize[1] - int( math.floor(self.boxSize[1] / 20.0 )),
                                     self.boxBorderColour)
        
        if self.sideways is False:
            divisionWidth = int( math.ceil(self.boxSize[1] / 10.0 ))        
            for i in xrange(0,self.boxSize[1],divisionWidth):
                # Right hand side line
                pygame.gfxdraw.hline(self.background,
                                     0,
                                     int( math.floor(self.boxSize[0] / 20.0 )),
                                     i,
                                     self.boxBorderColour)
                # Left hand side line
                pygame.gfxdraw.hline(self.background,
                                     self.boxSize[0],
                                     self.boxSize[0] - int( math.floor(self.boxSize[0] / 20.0 )),
                                     i,
                                     self.boxBorderColour)
        
    def _render(self):
        panel = self.background.copy()
        
        # Figure out bar size and off set
        barOff = self.barPadding
        maxBarSize = ( self.boxSize[0] - barOff * 2, self.boxSize[1] - ( barOff + self.boxBorderWidth ) )
        # Scale value to final size.
        barHeight = int ( maxBarSize[1] * ( self.getValue() / float(100) ) )       
        logging.debug("Bar Total Value {:03}, Scaled {}".format(self.value,barHeight))
        barColour = self.barColour
        if self.isClipped() is True:
            barColour = self.barColourClipped
        # Calculate bar details Top and Left
        barPosition = ( barOff, self.boxBorderWidth )
        barSize = ( self.boxSize[0] - barOff * 2, barHeight )
        if self.solid is not False:
            # Size each size of the point.
            barY = int( math.ceil( maxBarSize[1] / 60 ) )
            barPosition = ( barOff, barHeight - barY )
            barSize = (  self.boxSize[0] - barOff * 2, barY * 2 )
        # Now draw a box
        pygame.draw.rect(panel, barColour, (barPosition , barSize), 0)
        tPanel = pygame.transform.flip(panel,False,True)
        self.surface.blit(tPanel,self.boxPosition)

class BarIndicator(GenericIndicator):
    "Bar numerical data"
    def __init__(self,screen, Solid=True, Sideways=False):
        "Ininitializes a new BarGraph"
        GenericIndicator.__init__(self,screen)
        self.barColour = (0,255,0)
        self.barColourClipped = (255, 0, 0)
        self.digitalCount = 5
        self.solid = Solid
        self.sideways = Sideways
        
    def _draw_background(self):
        GenericIndicator._draw_background(self)
        # Draw outside box.
        pygame.draw.rect(self.background,
                         self.boxBorderColour,
                         ((0,0),self.boxSize),
                         self.boxBorderWidth)
        self.barPadding = int( math.ceil ( self.boxSize[0] / 20 ))
        
        # Draw scale marks.
        if self.sideways is True:
            divisionWidth = int( math.ceil(self.boxSize[0] / 10.0 ))        
            for i in xrange(0,self.boxSize[0],divisionWidth):
                # Bottom lines
                pygame.gfxdraw.vline(self.background,
                                     i,
                                     0,
                                     int( math.floor(self.boxSize[1] / 20.0 )),
                                     self.boxBorderColour)
                # Top lines
                pygame.gfxdraw.vline(self.background,
                                     i,
                                     self.boxSize[1],
                                     self.boxSize[1] - int( math.floor(self.boxSize[1] / 20.0 )),
                                     self.boxBorderColour)
        
        if self.sideways is False:
            divisionWidth = int( math.ceil(self.boxSize[1] / 10.0 ))        
            for i in xrange(0,self.boxSize[1],divisionWidth):
                # Right hand side line
                pygame.gfxdraw.hline(self.background,
                                     0,
                                     int( math.floor(self.boxSize[0] / 20.0 )),
                                     i,
                                     self.boxBorderColour)
                # Left hand side line
                pygame.gfxdraw.hline(self.background,
                                     self.boxSize[0],
                                     self.boxSize[0] - int( math.floor(self.boxSize[0] / 20.0 )),
                                     i,
                                     self.boxBorderColour)
        
    def _render(self):
        if not hasattr(self, 'background'):
            self._draw_background()
        if self.sideways is False:
            self._render_vertical()
        else:
            self._render_horizontal()
        self._render_overlay()

        
    def _render_horizontal(self):
        panel = self.background.copy()
        # Figure out bar size and off set
        barOff = self.barPadding
        
        maxBarSize = ( self.boxSize[0] - ( barOff + self.boxBorderWidth ), self.boxSize[1] - barOff * 2 )
        # Scale value to final size.
        barWidth = int ( maxBarSize[0] * ( self.getValue() / float(100) ) )       
        logging.debug("Bar Total Value {:03}, Scaled {}".format(self.value,barWidth))
        # Check for clipping
        barColour = self.barColour
        if self.isClipped() is True:
            barColour = self.barColourClipped

        # Calculate bar details 
        barPosition = ( self.boxBorderWidth, barOff )
        barSize = ( barWidth, self.boxSize[1] - barOff * 2 )
        
        if self.solid is False:
            # Size each size of the point.
            barX = int( math.ceil( maxBarSize[0] / 60 ) )
            barPosition = ( barWidth - barX, barOff )
            barSize = (  barX * 2, self.boxSize[1] - barOff * 2 )
        # Now draw a box
        pygame.draw.rect(panel, barColour, (barPosition , barSize), 0)
        tPanel = pygame.transform.flip(panel,False,True)
        self.surface.blit(tPanel,self.boxPosition)

    def _render_vertical(self):
        panel = self.background.copy()
        
        # Figure out bar size and off set
        barOff = self.barPadding
        maxBarSize = ( self.boxSize[0] - barOff * 2, self.boxSize[1] - ( barOff + self.boxBorderWidth ) )
        # Scale value to final size.
        barHeight = int ( maxBarSize[1] * ( self.getValue() / float(100) ) )       
        logging.debug("Bar Total Value {:03}, Scaled {}".format(self.value,barHeight))
        barColour = self.barColour
        if self.isClipped() is True:
            barColour = self.barColourClipped
        # Calculate bar details Top and Left
        barPosition = ( barOff, self.boxBorderWidth )
        barSize = ( self.boxSize[0] - barOff * 2, barHeight )
        if self.solid is False:
            # Size each size of the point.
            barY = int( math.ceil( maxBarSize[1] / 60 ) )
            barPosition = ( barOff, barHeight - barY )
            barSize = (  self.boxSize[0] - barOff * 2, barY * 2 )
        # Now draw a box
        pygame.draw.rect(panel, barColour, (barPosition , barSize), 0)
        tPanel = pygame.transform.flip(panel,False,True)
        self.surface.blit(tPanel,self.boxPosition)
        
    def _render_overlay(self):
        if self.render_overlay is False:
            return
        
        # overlay = pygame.Surface(self.boxSize,flags=pygame.HWSURFACE)
        # overlay = self.background.convert_alpha()
        # overlay.fill((0,0,0,0))
        
        # Figure out text size
        textSize = int( math.ceil( self.surface.get_height() / 10.0 ))
        if not hasattr(self, 'overlayFont'):
            # Create a font cache
            self.overlayFont = pygame.font.Font('fonts/destructobeambb_reg.ttf', textSize)
            
        curValue = self.getValue()
        # Put the text in a Var for later.
        Text = "{:03}".format(curValue)
        
        lineSize = self.overlayFont.get_linesize()
            
        if not hasattr(self, 'overlayCache'):
            self.overlayCache = dict()
                
        # Render the text, if it's not cached
        if Text in self.overlayCache:
            Label = self.overlayCache[Text]
        else:
            Label = self.overlayFont.render(Text, 1, (255,255,255))
            self.overlayCache[Text] = Label
                    
        # Blit to overlay
        posMe = ( ( self.boxSize[1] / 2.0 ) - ( Label.get_width() / 2.0 ),
                  self.surface.get_height() - textSize * 2 )
        
        self.surface.blit(Label,posMe)
                        

class DialIndicator(GenericIndicator):
    "Dial Graph is a thing apparently"
    def __init__(self,screen,offsetStyle=False, Sideways=True, Flip=False):
        "Ininitializes a new Dial"
        GenericIndicator.__init__(self,screen)
        self.boxBorderWidth = 0
        self.dialArmColour = (0,255,0)
        self.dialArmColourClipped = (255,0,0)
        self.offsetStyle = offsetStyle
        self.dialStart = -135
        self.dialSweep = 270
        self.sideways = Sideways
        self.flip = Flip
        if offsetStyle is True:
            self.dialStart = -30
            self.dialSweep = 60
        
    def _draw_background(self):
        GenericIndicator._draw_background(self)
        # Try and make a transparent background.
        self.background.fill((0,0,0,0))
        # Draw a background
        minWidth = self.boxSize[0]
        if minWidth > self.boxSize[1]:
            minWidth = self.boxSize[1]
        self.radius = int( math.floor( float( minWidth ) / 2 ) ) - 4
        self.circleCentre = (self.radius+3, self.radius+3)
        
        if self.offsetStyle is True:
            self.dialCentre = (self.radius+2, int( (self.radius+2) * 0.2))
            self.dialLength = int( float(self.radius) * 1.4 )
        else:
            self.dialCentre = self.circleCentre
            self.dialLength = int( float(self.radius) * 0.9 )

        # print("Setup Centre {}, Radius {}".format(self.circleCentre,self.radius))
        # print("Setup dialCentre {}, dialLength {}".format(self.dialCentre,self.dialLength))
        
        # Draw the background of the Dial
        pygame.gfxdraw.filled_circle(self.background,
                                     self.circleCentre[0],
                                     self.circleCentre[1],
                                     self.radius,
                                     self.boxBgColour)

        # Draw the border thicker as required.
        for i in xrange(self.boxBorderWidth):
            pygame.gfxdraw.aacircle(self.background,
                                    self.circleCentre[0],
                                    self.circleCentre[1],
                                    self.radius-i,
                                    self.boxBorderColour)
            
        dialZeroAngleRad  = math.radians(self.dialStart)
        dialMaxAngleRad  = math.radians(self.dialStart + self.dialSweep)
        # Draw an arc for the travel
        # print("Arc Dial Centre {}, Len {}".format(self.dialCentre,self.dialLength))
        # Figure out thickness for dial travel border
        thickness = int(self.radius * 0.05)
        # print("Radius {} -> Thickness {}".format(self.radius,thickness))        
        for i in xrange(thickness):
            pygame.gfxdraw.arc(self.background,
                               self.dialCentre[0],
                               self.dialCentre[1],
                               int(self.dialLength * 1.1) + i,
                               360 + 90 - ( self.dialStart + self.dialSweep ),
                               360 + 90 - self.dialStart,
                               self.boxBorderColour)

        # Draw Zero.
        zeroDeltaXp2 = int( self.dialLength * 1.1 * math.sin(dialZeroAngleRad) )
        zeroDeltaYp2 = int( self.dialLength * 1.1 * math.cos(dialZeroAngleRad) )
        dialZeroEndp2 = ( self.dialCentre[0] + zeroDeltaXp2,
                          self.dialCentre[1] + zeroDeltaYp2 )

        zeroDeltaXp1 = int( self.dialLength * math.sin(dialZeroAngleRad) )
        zeroDeltaYp1 = int( self.dialLength * math.cos(dialZeroAngleRad) )
        dialZeroEndp1 = ( self.dialCentre[0] + zeroDeltaXp1,
                          self.dialCentre[1] + zeroDeltaYp1 )
        pygame.draw.line(self.background,
                         self.boxBorderColour,
                         dialZeroEndp1,
                         dialZeroEndp2,
                         thickness)
        
        # Draw Max.
        maxDeltaXp2 = int( self.dialLength * 1.1 * math.sin(dialMaxAngleRad) )
        maxDeltaYp2 = int( self.dialLength * 1.1 * math.cos(dialMaxAngleRad) )
        dialMaxEndp2 = ( self.dialCentre[0] + maxDeltaXp2,
                          self.dialCentre[1] + maxDeltaYp2 )
        # Blank out the central part of the max line
        maxDeltaXp1 = int( self.dialLength * math.sin(dialMaxAngleRad) )
        maxDeltaYp1 = int( self.dialLength * math.cos(dialMaxAngleRad) )
        dialMaxEndp1 = ( self.dialCentre[0] + maxDeltaXp1,
                          self.dialCentre[1] + maxDeltaYp1 )
        pygame.draw.line(self.background,
                         self.boxBorderColour,
                         dialMaxEndp2,
                         dialMaxEndp1,
                         thickness)

        
        divisionWidth = (dialMaxAngleRad - dialZeroAngleRad) /10.0
        fSeq = self._get_float_range(dialZeroAngleRad,dialMaxAngleRad,divisionWidth)
        # print "Start {}, End {}, Steps {:f}".format(dialZeroAngleRad,dialMaxAngleRad,divisionWidth)
        for i in fSeq:
            picDeltaXp2 = int( self.dialLength * 1.1 * math.sin(i) )
            picDeltaYp2 = int( self.dialLength * 1.1 * math.cos(i) )
            dialPicEndp2 = ( self.dialCentre[0] + picDeltaXp2,
                             self.dialCentre[1] + picDeltaYp2 )
            # Blank out the central part of the max line
            picDeltaXp1 = int( self.dialLength * math.sin(i) )
            picDeltaYp1 = int( self.dialLength * math.cos(i) )
            dialPicEndp1 = ( self.dialCentre[0] + picDeltaXp1,
                             self.dialCentre[1] + picDeltaYp1 )
            pygame.draw.line(self.background,
                             self.boxBorderColour,
                             dialPicEndp2,
                             dialPicEndp1,
                             thickness)
        

    def _render(self):
        if not hasattr(self, 'background'):
            self._draw_background()
        panel = self.background.copy()
        # Draw new line
        # print "Rad {} Length {}".format(self.radius,self.dialLength)
        dialArmColour = self.dialArmColour
        if self.isClipped() is True:
            dialArmColour = self.dialArmColourClipped
        dialAngle  = (( self.getValue() / float(100) ) * self.dialSweep ) + self.dialStart
        dialAngleRad  = math.radians(dialAngle)
        deltaX = int( self.dialLength * math.sin(dialAngleRad) )
        deltaY = int( self.dialLength * math.cos(dialAngleRad) )
        dialEnd = ( self.dialCentre[0] + deltaX, self.dialCentre[1] + deltaY )
        pygame.draw.line(panel,
                         dialArmColour,
                         self.dialCentre,
                         dialEnd,
                         2)
        logging.debug("Dial Value {:03}, Angle {}, X,Y {},{}".format(self.value,dialAngle,deltaX,deltaY))
        tPanel = pygame.transform.flip(panel,False,True)
        if self.sideways is True and self.offsetStyle is True:
            tPanel = pygame.transform.rotate(tPanel,90)
        if self.flip is True and self.offsetStyle is True:
            tPanel = pygame.transform.flip(tPanel,True,False)            
        self.surface.blit(tPanel,self.boxPosition)
        self._render_overlay()        
        
    def _render_overlay(self):
        if self.render_overlay is False:
            return
        
        # overlay = pygame.Surface(self.boxSize,flags=pygame.HWSURFACE)
        # overlay = self.background.convert_alpha()
        # overlay.fill((0,0,0,0))
        
        # Figure out text size
        textSize = int( math.ceil( self.surface.get_height() / 10.0 ))
        if not hasattr(self, 'overlayFont'):
            # Create a font cache
            self.overlayFont = pygame.font.Font('fonts/destructobeambb_reg.ttf', textSize)
            
        curValue = self.getValue()
        # Put the text in a Var for later.
        Text = "{:03}".format(curValue)
        
        lineSize = self.overlayFont.get_linesize()
            
        if not hasattr(self, 'overlayCache'):
            self.overlayCache = dict()
                
        # Render the text, if it's not cached
        if Text in self.overlayCache:
            Label = self.overlayCache[Text]
        else:
            Label = self.overlayFont.render(Text, 1, (255,255,255))
            self.overlayCache[Text] = Label
                    
        # Blit to overlay
        posMe = ( ( self.boxSize[1] / 2.0 ) - ( Label.get_width() / 2.0 ),
                  self.surface.get_height() - textSize * 2 )
        
        # overlay.blit(Label,posMe)
        
        self.surface.blit(Label,posMe)





        
