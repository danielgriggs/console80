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

def _calculate_vector(vec):
    return math.sqrt( vec[0]**2 + vec[1]**2 )

def _get_float_range(start,stop,step):
    r = start
    while r < stop:
        yield r
        r += step


class MainScreen:
    screen = None;

    def __init__(self, hw=True):
        "Ininitializes a new pygame screen using the framebuffer"

        # Setup logging early on
        # logging.basicConfig(level=logging.DEBUG)

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
        # flags |= pygame.ASYNCBLIT
        if hw is True:
            flags |= pygame.HWSURFACE

        self.hw_surface = hw

        # Create a surface.
        self.screen = pygame.display.set_mode(size, flags)
        # Initialise a font?
        pygame.font.init()

        # Setup basic colours and borders.
        self.screen_bg_colour = (50,50,50)
        self.wScreenBorderWidth = 5
        self.wScreenBgColour = (50,50,50)

        # Clear the screen to start
        # self.screen.fill((0,0,0))
        # Store the Working Window Size.
        self.wSize = (size[0] - (self.wScreenBorderWidth*2),
                      size[1] - (self.wScreenBorderWidth*2))
        # Generate a working screen.
        self.wScreen = self.screen.subsurface((self.wScreenBorderWidth,
                                               self.wScreenBorderWidth,
                                               self.wSize[0],
                                               self.wSize[1]))
        # Fill it with a colour!
        self.wScreen.fill(self.screen_bg_colour)

        # Leave some space for some dials
        self.dials = []

        # Render the screen
        pygame.display.update()

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def create_clock(self):
        return pygame.time.Clock()

    def redraw_screen(self):
        logging.info("Flipping screen")
        pygame.display.flip()

    def get_panel_space(self,panel_spec):
        # TODO: Check for collisions.

        # Generate a subsurface for this panel..
        panel_surface = {}
        logging.debug("Creating panel {} in surface {}".format(panel_spec['panel_spec'],self.wScreen.get_rect()))
        panel_surface['panel'] = self.wScreen.subsurface(panel_spec['panel_spec'])

        # If label is required, create it.
        if 'label_spec' in panel_spec:
            logging.debug("Creating label {} in surface.".format(panel_spec['label_spec']))
            panel_surface['label'] = self.wScreen.subsurface(panel_spec['label_spec'])

        # return the surface
        return panel_surface

    def add_panel(self,panel_spec):
        # Create subsurface for panel
        surfaces = self.get_panel_space(panel_spec)
        if panel_spec['type'] == 'bar':
            dial = BarIndicator(surfaces,panel_spec)
        elif panel_spec['type'] == 'dial':
            dial = DialIndicator(surfaces,panel_spec)
        elif panel_spec['type'] == 'point':
            dial = ScatterIndicator(surfaces,panel_spec)

        self.dials.append(dial)
        return dial

    def auto_layout_panels(self,panels=(4,3),label=0):
        "Figure out dimensions for how big the panels are and generates and array of panels."
        "Takes a simple tuple of columns by rows."

        # calculate maximum column width.
        column_size = self.wSize[0] / float(panels[0]) - 1
        logging.debug("Column size is {} / {} = {}".format(self.wSize[0],panels[0],column_size))
        row_size = int ( self.wSize[1] / float(panels[1]) ) - 1
        logging.debug("Row size is {} / {} = {}".format(self.wSize[1],panels[1],row_size))

        # Calculate vertical size including label
        p_size = int( row_size * ( 1.00 / (1.00 + label) ) )
        l_size = int ((row_size - p_size) / 2.0 ) * 2
        logging.debug("p_size {}, l_size {}".format(p_size,l_size))

        # We need the smaller of the two
        max_size = column_size
        if column_size > p_size:
            max_size = p_size

        # Also make the maxSize divisiable by two.
        half_width = math.floor(max_size / 2.0)
        max_size = int ( half_width * 2 )
        logging.debug("choosen max size of side is {}".format(max_size))

        # Calculate the space between panels horizontally.
        x_leftover = self.wSize[0] - (panels[0] * max_size)
        x_buffer = x_leftover / float(panels[0] + 1)
        x_offset = int( math.floor(x_buffer + max_size))
        logging.debug("x: left {} buffer {} offset {}".format(x_leftover,x_buffer,x_offset))

        # Calculate the space between panels vertically.
        # y_size because we need to account for labels.
        y_size = max_size + l_size
        y_leftover = self.wSize[1] - (panels[1] * y_size)
        y_buffer = y_leftover / float(panels[1] + 1)
        y_offset = int ( math.floor(y_buffer + y_size) )
        logging.debug("y: left {} buffer {} offset {}".format(y_leftover,y_buffer,y_offset))

        logging.debug("Space between panels X:{} Y:{}".format(x_buffer,y_buffer))

        # create an array for panels.
        panelPositions = []
        for y in xrange(panels[1],0,-1):
            for x in xrange(1,panels[0]+1,1):
                x_pos = int( x_offset * x ) - max_size
                y_pos = int( y_offset * y ) - y_size
                position = { "panel_spec" : (x_pos, y_pos, max_size, max_size), \
                             "rpos" : (x, y)}
                if l_size > 0:
                    position['label_spec'] = (x_pos, y_pos + max_size, \
                                                max_size, l_size)
                logging.debug("New panel {} {}".format(x_pos,y_pos))
                panelPositions.append(position)
        return panelPositions

class commonPanel(object):

    def __init__(self,surfaces,panel_spec):
        "Ininitializes basic panel data"
        # Store a reference to the screen.
        # self.screen = screen
        # self.rect = rect
        self.surfaces = surfaces
        # Label Settings
        self.label_text = "No Label"
        if 'label_text' in panel_spec:
            self.label_text = panel_spec['label_text']
        # Hardware acceleration
        self.hw_surface = False
        if 'hw_surface' in panel_spec:
            self.hw_surface = panel_spec['hw_surface']
        self.label_text_colour = (255,255,255)
        self.label_border_width = 0
        self.label_border_colour = (255,255,255)
        self.label_bg_colour = (50,50,50)
        self.label_exists = False
        # Box settings
        self.border_width = 1
        self.border_colour = (255,255,255)
        self.bg_colour = (100,100,100)
        self.name = "GenericPanel"
        self.render_overlay = False
        if 'render_overlay' in panel_spec:
            self.render_overlay = panel_spec['render_overlay']

        if 'label' in self.surfaces:
            self.label_exists = True
            self._draw_label()

    def _draw_background(self):
        "Internal method for regenerating the background"
        # Fill up the background with a colour.
        self.surfaces['panel'].fill(self.bg_colour)
        # Border width is centered, needs
        # border width/2 offset
        self.panel_size = self.surfaces['panel'].get_size()
        #if self.border_width > 0:
        #    pygame.draw.rect(self.surfaces['panel'],
        #                     self.border_colour,
        #                     self.surfaces['panel'].get_rect(),
        #                     self.border_width)
        flags = 0
        if self.hw_surface is True:
            flags |= pygame.HWSURFACE
        self.background = pygame.Surface(self.panel_size,flags=flags)

        # print("Surface flags {:#x}".format(self.background.get_flags()))
        self.background = self.background.convert_alpha()
        # print("{:#x}".format(self.background.get_flags()))

    def _draw_label(self):
        if self.label_exists:
            # Fill the label with background colour
            logging.debug(self.surfaces['label'])
            self.surfaces['label'].fill(self.label_bg_colour)
            # render a box with text
            if not hasattr(self, 'label_font'):
                boxHeight = int( math.floor( self.surfaces['panel'].get_height() ))
                self.label_font = pygame.font.Font('fonts/Impact Label Reversed.ttf', boxHeight)
            Text = self.label_font.render(self.label_text,
                                          1,
                                          self.label_text_colour,
                                          self.label_bg_colour)
            # Even though this is called once it effects the
            # long term running of the code?!
            # Seems to be about 574 vs 568 speed difference
            if True:
                # Convert to display format (faster, also allows scaling)
                Text = Text.convert()
                textRect = Text.get_rect()
                # Get the Label size
                panelLabelRect = self.surfaces['label'].get_rect()
                # Scale it inside
                scaledSize = textRect.fit(panelLabelRect)
                # transform and copy.
                scaledText = pygame.transform.smoothscale(Text,scaledSize.size)
                self.surfaces['label'].blit(scaledText,scaledSize)
            else:
                self.surfaces['label'].blit(Text,(0,0))

    def set_bg_colour(self,colour):
        self.bg_colour = colour
        self._draw_background()

    def render_overlay(self,render=None):
        "Set whether the overlay should rendered, returns current status."
        # print("Setting render overlay to {}".format(Render))
        if render is not None:
            self.render_overlay = render
        return self.render_overlay

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

class SingleIntValue(object):

    def __init__(self,Min=0,Value=0,Max=100,maxHistory=5):
        "Create a place to store and manipulate a value"
        # Store a reference to the screen.
        self._value = Value
        self._valueSweep = 1
        self._valueHistory = []
        self._maxHistory = maxHistory
        self._maxValue = Max
        self._minValue = Min

    def __repr__(self):
        strm = "Min={}/".format(self._minValue)
        strm += "Value={}/".format(self._value)
        strm += "Max={}/".format(self._maxValue)
        strm += "ScaledVaule={}".format(self.getScaledValue())
        strm += ", History {}: {}".format(self._maxHistory,self._valueHistory)
        return strm

    def hist_length(self,value=None):
        "Set the max value history log"
        if value is not None and int(value) > -1:
            self._maxHistory = value
        return self._maxHistory

    def hist_max(self):
        "Get the max value from the history"
        if self._maxHistory is 0:
            return None
        return max(self._valueHistory)

    def hist_min(self):
        "Get the min value from the history"
        if self._maxHistory is 0:
            return None
        return min(self._valueHistory)

    def hist_avg(self):
        "Get the average of all history items"
        if self._maxHistory is 0:
            return None
        floatAvg = sum( self._valueHistory ) / float(len(self._valueHistory))
        return floatAvg

    def hist_last(self,Num=1):
        "Get the Num previous values"
        if self._maxHistory is 0:
            return None
        histLength = len(self._valueHistory)
        if Num > histLength:
            Num = histLength
        start = histLength - Num
        # print "Get history {} {}".format(start,histLength)
        return self._valueHistory[start:histLength]

    def value_get(self):
        "Return the current clipped value"
        if self._value > self._maxValue:
            return self._maxValue
        elif self._value < self._minValue:
            return self._minValue
        else:
            return self._value

    def value_get_raw(self):
        "Return the current clipped value"
        return self._value

    def value_update(self,value):
        "Update the current value"
        # Record current value to history
        if self._maxHistory is not 0:
            self._valueHistory.append(self._value)
        # Record new value
        self._value = value
        # Clear history
        while len(self._valueHistory) > self._maxHistory:
            self._valueHistory.pop(0)
        # print("Value updated to {}".format(value))
        self._render()

    def value_rand(self):
        newValue = random.randint(self._minValue, self._maxValue)
        # Record new value
        self.value_update(newValue)

    def value_rand_step(self):
        # Get the current value
        curValue = self.value_get()
        newValue = curValue + random.randint(-1, 1)
        # Record new value
        self.value_update(newValue)

    def value_sweep(self):
        # Get the current value
        curValue = self._value
        newValue = curValue + self._valueSweep
        # Record new value
        self.value_update(newValue)
        # If we are clipping then reverse
        if self.value_clipped(10) is True:
            self._valueSweep *= -1

    def getScaledValue(self,Max=1000):
        "Return the current clipped value between 0 and Max"
        # Clip the Value
        clippedValue = self._value
        if self._value > self._maxValue:
            clippedValue = self._maxValue
        elif self._value < self._minValue:
            clippedValue = self._minValue

        # normalise
        normalClippedValue = float( clippedValue - self._minValue )
        normalMax = float( self._maxValue - self._minValue )
        # Bypass divide by 0 issues
        if int(normalClippedValue) is 0:
            return 0
        # Scale the value to a value
        scaled_value = int(( normalClippedValue / normalMax ) * Max)
        logging.debug("get_scaled returns {} from {}".format(scaled_value,clippedValue))
        return scaled_value

    def value_range_set(self,Range=None):
        "Set the accepted input range as a tuple (low,high)"
        if Range is not None:
            self._maxValue = Range[1]
            self._minValue = Range[0]

        return (self._minValue,self._maxValue)

    def value_clipped(self, margin=0):
        "Return whether the current value is clipped"
        if self._value <= self._maxValue + margin:
            if self._value >= self._minValue - margin:
                return False
        return True

class MultiIntValue(object):

    def __init__(self,Min=0,Value=0,Max=100,maxHistory=5,):
        "Create a place to store and manipulate a value"
        # Store a reference to the screen.
        self._value = Value
        self._valueSweep = 1
        self._valueHistory = []
        self._maxHistory = maxHistory
        self._maxValue = Max
        self._minValue = Min

    def __repr__(self):
        strm = "Min={}/".format(self._minValue)
        strm += "Value={}/".format(self._value)
        strm += "Max={}/".format(self._maxValue)
        strm += "ScaledVaule={}".format(self.getScaledValue())
        strm += ", History {}: {}".format(self._maxHistory,self._valueHistory)
        return strm

    def hist_length(self,value=None):
        "Set the max value history log"
        if value is not None and int(value) > -1:
            self._maxHistory = value
        return self._maxHistory

    def hist_max(self):
        "Get the max value from the history"
        if self._maxHistory is 0:
            return None
        return max(self._valueHistory)

    def hist_min(self):
        "Get the min value from the history"
        if self._maxHistory is 0:
            return None
        return min(self._valueHistory)

    def hist_avg(self):
        "Get the average of all history items"
        if self._maxHistory is 0:
            return None
        floatAvg = sum( self._valueHistory ) / float(len(self._valueHistory))
        return floatAvg

    def hist_last(self,Num=1):
        "Get the Num previous values"
        if self._maxHistory is 0:
            return None
        histLength = len(self._valueHistory)
        if Num > histLength:
            Num = histLength
        start = histLength - Num
        # print "Get history {} {}".format(start,histLength)
        return self._valueHistory[start:histLength]

    def value_get(self):
        "Return the current clipped value"
        if self._value > self._maxValue:
            return self._maxValue
        elif self._value < self._minValue:
            return self._minValue
        else:
            return self._value

    def value_get_raw(self):
        "Return the current clipped value"
        return self._value

    def value_update(self,value):
        "Update the current value"
        # Record current value to history
        if self._maxHistory is not 0:
            self._valueHistory.append(self._value)
        # Record new value
        self._value = value
        # Clear history
        while len(self._valueHistory) > self._maxHistory:
            self._valueHistory.pop(0)
        # print("Value updated to {}".format(value))
        self._render()

    def value_rand(self):
        newValue = random.randint(self._minValue, self._maxValue)
        # Record new value
        self.value_update(newValue)

    def value_rand_step(self):
        # Get the current value
        curValue = self.value_get()
        newValue = curValue + random.randint(-1, 1)
        # Record new value
        self.value_update(newValue)

    def value_sweep(self):
        # Get the current value
        curValue = self._value
        newValue = curValue + self._valueSweep
        # Record new value
        self.value_update(newValue)
        # If we are clipping then reverse
        if self.value_clipped(10) is True:
            self._valueSweep *= -1

    def getScaledValue(self,Max=1000):
        "Return the current clipped value between 0 and Max"
        # Clip the Value
        clippedValue = self._value
        if self._value > self._maxValue:
            clippedValue = self._maxValue
        elif self._value < self._minValue:
            clippedValue = self._minValue

        # normalise
        normalClippedValue = float( clippedValue - self._minValue )
        normalMax = float( self._maxValue - self._minValue )
        # Bypass divide by 0 issues
        if int(normalClippedValue) is 0:
            return 0
        # Scale the value to a value
        scaled_value = int(( normalClippedValue / normalMax ) * Max)
        logging.debug("get_scaled returns {} from {}".format(scaled_value,clippedValue))
        return scaled_value

    def value_range_set(self,Range=None):
        "Set the accepted input range as a tuple (low,high)"
        if Range is not None:
            self._maxValue = Range[1]
            self._minValue = Range[0]

        return (self._minValue,self._maxValue)

    def value_clipped(self, margin=0):
        "Return whether the current value is clipped"
        if self._value <= self._maxValue + margin:
            if self._value >= self._minValue - margin:
                return False
        return True

class SingleCoordValue(object):

    def __init__(self):
        "Create a place to store and manipulate co-ordinate value"
        # Store a reference to the screen.
        self._value = None
        self._value_min = (0,0)
        self._value_max = (100,100)
        self._value_sweep = [1, 1]
        self._value_history = []
        self._max_history = 5

    def __repr__(self):
        strm = "Min={}/".format(self._valueMin)
        strm += "Value={}/".format(self._value)
        strm += "Max={}".format(self._valueMax)
        strm += ", History {}: {}".format(self._maxHistory,self._valueHistory)
        return strm

    def hist_length(self,value=None):
        "Set the max value history log"
        if value is not None and int(value) > -1:
            self._max_history = value
        return self._max_history

    def hist_max(self):
        "Get the max value from the history"
        if self._max_history is 0:
            return None
        max = (0,0)
        for i in self._value_history:
            if _calculate_vector(i) > _calculate_vector(max):
                max = i
        return max

    def hist_min(self):
        "Get the min value from the history"
        if self._max_history is 0:
            return None
        min = (0,0)
        for i in self._value_history:
            if _calculate_vector(i) < _calculate_vector(min):
                min = i
        return min

    def hist_avg(self):
        "Get the average of all history items"
        if self._max_history is 0:
            return None
        c = [0,0]
        l = len(self._value_history)
        for i in self._value_history:
            c[0] += i[0]
            c[1] += i[1]
        return (c[0]/l, c[1]/l)

    def hist_last(self,Num=1):
        "Get the Num previous values"
        if self._max_history is 0:
            return None
        histLength = len(self._value_history)
        if Num > histLength:
            Num = histLength
        start = histLength - Num
        # print "Get history {} {}".format(start,histLength)
        return self._value_history[start:histLength]

    def value_get(self):
        "Return the current value clipped"
        returnValue = [None, None]
        for axis in [0, 1]:
            if self._value[axis] > self._value_max[axis]:
                returnValue[axis] = self._value_max[axis]
            elif self._value[axis] < self._value_min[axis]:
                returnValue[axis] = self._value_min[axis]
            else:
                returnValue[axis] = self._value[axis]
        return returnValue

    def value_get_raw(self):
        "Return the current value without clipping"
        return self._value

    def value_update(self,value):
        "Update the current value"
        if not isinstance(value, tuple) or len(value) != 2:
            raise TypeError("This should be co-ordinates")
        # Record current value to history
        self._value_history.append(self._value)
        # Record new value
        self._value = value
        # Clear history
        while len(self._value_history) > self._max_history:
            self._value_history.pop(0)
        self._render()

    def value_rand(self):
        "modify the current value to a random amount"

        newValueX = random.randint(self._value_min[0], self._value_max[0])
        newValueY = random.randint(self._value_min[1], self._value_max[1])
        # Record new value
        self.value_update((newValueX,newValueY))

    def value_rand_step(self):
        "modify the current value by a random amount"
        # Get the current value
        curValue = self.value_get()
        newValueX = curValue[0] + random.randint(-1, 1)
        newValueY = curValue[1] + random.randint(-1, 1)
        # Record new value
        self.value_update((newValueX,newValueY))

    def value_sweep(self):
        "modify the current value by a random amount"
        # Get the current value
        cur_value = self._value
        new_value_x = cur_value[0] + self._value_sweep[0]
        new_value_y = cur_value[1] + self._value_sweep[1]
        # Record new value
        self.value_update((new_value_x,new_value_y))
        # If clipped sweep back
        clipped = self.value_clipped(10)
        for axis in [0, 1]:
            if clipped[axis] is True:
                self._value_sweep[axis] *= -1

    def value_range_set(self,Range):
        "Set the accepted input range as a tuple (low,high)"
        self._valueMax = Range[1]
        self._valueMin = Range[0]

    def value_clipped(self, margin=0):
        "Return whether the current value is clipped"
        clipping = [True, True]
        for axis in [0, 1]:
            if self._value[axis] <= self._value_max[axis] + margin:
                if self._value[axis] >= self._value_min[axis] - margin:
                    clipping[axis] = False

        return clipping

class ScatterIndicator(commonPanel, SingleCoordValue):
    "Scatter Graph for lack of a better name"

    def __init__(self, screen, panel_spec):
        "Ininitializes a new scatter graph"
        commonPanel.__init__(self, screen, panel_spec)
        SingleCoordValue.__init__(self)
        # axisZero for   X,Y
        self.axis = { 'max' : (100, 100),
                      'min' : (0, 0),
                      'zero' : (50,50),
                      'width' : 1,
                      'colour' : (255,255,255) }

        self.point = { 'colour' : (0,255,0),
                       'colour_clipped' : (255,0,0),
                       'radius' : 5,
                       'outline' : 1 }

    def _draw_background(self):
        commonPanel._draw_background(self)

        # Draw outside box.
        if self.border_width > 0:
            pygame.draw.rect(self.background,
                             self.border_colour,
                             self.background.get_rect(),
                             self.border_width)

        box_size = self.background.get_size()
        # Draw the X Axis, at the Y
        # maxYRange = self.maxValue[1] - self.minValue[1]
        max_y_range = self.axis['max'][1] - self.axis['min'][1]
        # normZeroOnY = self.axisZero[1] - self.minValue[1]
        zero_on_y = self.axis['zero'][1] - self.axis['min'][1]

        logging.debug("axis['zero'][1] = {} " \
                      "self.axis['min'][1] = {}".format(self.axis['zero'][1],
                                                        self.axis['min'][1]))
        logging.debug("box_size[0] {} " \
                      "max_y_range {} " \
                      "zero_on_y {}".format(box_size[0],
                                            max_y_range,
                                            zero_on_y))
        scaled_x_zero = int( box_size[1] * ( zero_on_y / float(max_y_range) ) ) - 1
        logging.debug("  Draw from {},{} to {},{}".format(0,
                                                          scaled_x_zero,
                                                          box_size[0]-1,
                                                          scaled_x_zero))
        pygame.draw.line(self.background,
                         self.axis['colour'],
                         (0, scaled_x_zero),
                         (box_size[0]-1, scaled_x_zero),
                         self.axis['width'])

        # Draw the Y Axis, at the X
        # maxXRange   = self.maxValue[0] - self.minValue[0]
        max_x_range = self.axis['max'][0] - self.axis['min'][0]
        # normZeroOnX = self.axisZero[0] - self.minValue[0]
        zero_on_x = self.axis['zero'][0] - self.axis['min'][0]

        logging.debug("box_size[1] {} " \
                      "max_x_range {} " \
                      "zero_on_x {}".format(box_size[1],
                                            max_x_range,
                                            zero_on_x))
        scaled_y_zero = int( box_size[0] * ( zero_on_y / float(max_x_range) ) ) - 1
        logging.debug("  Draw from {},{} to {},{}".format(scaled_y_zero,
                                                          0,
                                                          scaled_y_zero,
                                                          box_size[1]-1))
        pygame.draw.line(self.background,
                         self.axis['colour'],
                         (scaled_y_zero, 0),
                         (scaled_y_zero, box_size[1]-1),
                         self.axis['width'])

        # Decide how big the circle should be.
        self.pointRadius = int( math.ceil(max_x_range / 20 ))

        # Line length for sub markers.
        lineLength = int( math.ceil( box_size[1] / 50 ))

        # Draw little lines along the vertical axis.
        divisionsDist = int( math.ceil( scaled_y_zero / 10.0 )) * 2
        for i in xrange(scaled_y_zero, box_size[1], divisionsDist):
            pygame.gfxdraw.hline(self.background,
                                 scaled_x_zero - lineLength,
                                 scaled_x_zero + lineLength,
                                 i,
                                 self.border_colour)
        for i in xrange(scaled_y_zero, 0, -divisionsDist):
            pygame.gfxdraw.hline(self.background,
                                 scaled_x_zero - lineLength,
                                 scaled_x_zero + lineLength,
                                 i,
                                 self.border_colour)

        # Draw little lines along the horizontal axis.
        divisionsDist = int( math.ceil( scaled_x_zero / 10.0 )) * 2
        for i in xrange(scaled_x_zero, box_size[0], divisionsDist):
            pygame.gfxdraw.vline(self.background,
                                 i,
                                 scaled_y_zero - lineLength,
                                 scaled_y_zero + lineLength,
                                 self.border_colour)
        for i in xrange(scaled_x_zero, 0, -divisionsDist):
            pygame.gfxdraw.vline(self.background,
                                 i,
                                 scaled_y_zero - lineLength,
                                 scaled_y_zero + lineLength,
                                 self.border_colour)

    def _render(self):
        if not hasattr(self, 'background'):
            self._draw_background()
        panel = self.background.copy()
        value = self.value_get()
        box_size = panel.get_size()

        max_y_range = self._value_max[1] - self._value_min[1]
        norm_value_y = value[1] - self._value_min[1]
        scaled_y = int( box_size[1] * ( norm_value_y / float(max_y_range) ) )

        # Calculate X value
        max_x_range = self._value_max[0] - self._value_min[0]
        norm_value_x = value[0] - self._value_min[0]
        scaled_x = int( box_size[0] * ( norm_value_x / float(max_x_range) ) )

        pointColour = self.point['colour']
        pointOutline = self.point['outline']
        clipped = self.value_clipped()
        for axis in [0, 1]:
            if clipped[axis] is True:
                pointColour = self.point['colour_clipped']
                pointOutline  = 0

        pygame.draw.circle(panel,
                           pointColour, # Colour
                           (scaled_x,scaled_y), # Circle Centre
                           self.point['radius'], # Radius
                           pointOutline) # line width Zero for fill
        tPanel = pygame.transform.flip(panel,False,True)
        self.surfaces['panel'].blit(tPanel,(0,0))
        self._render_overlay()

    def _render_overlay(self):
        if self.render_overlay is False:
            return

        # overlay = pygame.Surface(self.boxSize,flags=pygame.HWSURFACE)
        # overlay = self.background.convert_alpha()
        # overlay.fill((0,0,0,0))

        # Figure out text size
        text_size = int( math.ceil( self.surfaces['panel'].get_width() / 15.0 ))
        if not hasattr(self, 'overlay_font'):
            # Create a font cache
            self.overlay_font = pygame.font.Font('fonts/destructobeambb_reg.ttf', text_size)

        cur_value = self.value_get()
        raw_value = self.value_get_raw()
        # Put the text in a Var for later.
        x_text = "X {:03}".format(cur_value[0])
        y_text = "Y {:03}".format(cur_value[1])
        line_size = self.overlay_font.get_linesize()

        if not hasattr(self, 'overlay_cache'):
            self.overlay_cache = [dict(),dict()]

        clipped = self.value_clipped()

        # Render the text, if it's not cached
        if raw_value[0] in self.overlay_cache[0]:
            x_label = self.overlay_cache[0][raw_value[0]]
        else:
            textc = self.point['colour']
            if clipped[0]:
                textc = self.point['colour_clipped']
            x_label = self.overlay_font.render(x_text, 1, textc, (0,0,0))
            self.overlay_cache[0][raw_value[0]] = x_label

        if raw_value[1] in self.overlay_cache[1]:
            y_label = self.overlay_cache[1][raw_value[1]]
        else:
            textc = self.point['colour']
            if clipped[1]:
                textc = self.point['colour_clipped']
            y_label = self.overlay_font.render(y_text, 1, textc, (0,0,0))
            self.overlay_cache[1][raw_value[1]] = y_label

        # Blit to overlay
        # overlay.blit(xLabel,(textSize,textSize))
        # overlay.blit(yLabel,(textSize,textSize + lineSize ))
        # self.surface.blit(overlay,self.boxPosition)

        # Try direct blit with no overlay.
        self.surfaces['panel'].blit(x_label,(text_size,text_size))
        self.surfaces['panel'].blit(y_label,(text_size,text_size + line_size ))

class DigitalIndicator(commonPanel):
    "Digital numerical data"

    def __init__(self, screen, panel_spec):
        "Ininitializes a new BarGraph"
        commonPanel.__init__(self,screen)
        self.digit = { 'colour' : (0,255,0) }
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

    def _render(self):
        panel = self.background.copy()

        self.surface.blit(tPanel,self.boxPosition)

class BarIndicator(commonPanel, SingleIntValue):
    "Bar numerical data"

    def __init__(self, surfaces, panel_spec):
        "Ininitializes a new BarGraph"
        logging.debug(panel_spec)
        commonPanel.__init__(self, surfaces, panel_spec)
        SingleIntValue.__init__(self)
        self.bar_colour = (0,255,0)
        self.bar_colour_clipped = (255, 0, 0)
        # self.digitalCount = 5
        self.solid = True
        if 'solid' in panel_spec:
            self.solid = panel_spec['solid']

        self.sideways = False
        if 'sideways' in panel_spec:
            self.sideways = panel_spec['sideways']

        self.flip = False
        if 'flip' in panel_spec:
            self.flip = panel_spec['flip']

        self._render()

    def _draw_background(self):
        commonPanel._draw_background(self)
        # Draw outside box.
        pygame.draw.rect(self.background,
                         self.border_colour,
                         ((0,0),self.panel_size),
                         self.border_width)
        if self.sideways is True:
            padding = int( math.ceil ( self.panel_size[1] / 20 )) \
                      + self.border_width
            self.barXYPadding = ( self.border_width, padding )
        else:
            padding = int( math.ceil ( self.panel_size[0] / 20 )) \
                      + self.border_width
            self.barXYPadding = ( padding, self.border_width )

        # Draw scale marks.
        if self.sideways is True:
            divisionWidth = int( math.ceil(self.panel_size[0] / 10.0 ))
            for i in xrange(0,self.panel_size[0],divisionWidth):
                # Bottom lines
                pygame.gfxdraw.vline(self.background,
                                     i,
                                     0,
                                     int( math.floor(self.panel_size[1] / 20.0 )),
                                     self.border_colour)
                # Top lines
                pygame.gfxdraw.vline(self.background,
                                     i,
                                     self.panel_size[1],
                                     self.panel_size[1] - int( math.floor(self.panel_size[1] / 20.0 )),
                                     self.border_colour)

        if self.sideways is False:
            divisionWidth = int( math.ceil(self.panel_size[1] / 10.0 ))
            for i in xrange(0,self.panel_size[1],divisionWidth):
                # Right hand side line
                pygame.gfxdraw.hline(self.background,
                                     0,
                                     int( math.floor(self.panel_size[0] / 20.0 )),
                                     i,
                                     self.border_colour)
                # Left hand side line
                pygame.gfxdraw.hline(self.background,
                                     self.panel_size[0],
                                     self.panel_size[0] - int( math.floor(self.panel_size[0] / 20.0 )),
                                     i,
                                     self.border_colour)

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
        panelSize = panel.get_size()
        # Figure out bar size and off set
        barMin = self.barXYPadding
        maxBarSize = ( panelSize[0] - barMin[0] * 2,
                       panelSize[1] - barMin[1] * 2 )
        value = self.value_get()

        if self.solid is True:
            # Scale value to final size.
            barWidth = int( maxBarSize[0] * ( value / float(100) ) )
            logging.debug("Bar Total Value {:03}, Scaled {}".format(value,barWidth))

            # Calculate bar details Top and Left
            barPosition = barMin
            barSize = (barWidth, maxBarSize[1])
        else:
            # Line width divided by two
            barX = int( math.ceil( maxBarSize[0] / 60 ) )

            # Recalculate
            barMin = (self.barXYPadding[0] - barX,
                      self.barXYPadding[1] )

            # Calculate middle of bar.
            barWidth = int( maxBarSize[0] * ( value / float(100) ) ) - barX

            # To be fair I don't understand why I only add the padding
            # it should be BarMin[1]
            barPosition = ( barWidth + self.barXYPadding[0], barMin[1] )
            barSize = (barX * 2 , maxBarSize[1])

        # Check for clipping
        barColour = self.bar_colour
        if self.value_clipped() is True:
            barColour = self.bar_colour_clipped

        # Draw a box
        pygame.draw.rect(panel, barColour, (barPosition , barSize), 0)

        if self.flip is True:
            panel = pygame.transform.flip(panel,True,False)
        self.surfaces['panel'].blit(panel,(0,0))

    def _render_vertical(self):
        panel = self.background.copy()
        panelSize = panel.get_size()
        # Figure out bar size and off set
        barMin = self.barXYPadding
        maxBarSize = ( panelSize[0] - barMin[0] * 2,
                       panelSize[1] - barMin[1] * 2 )
        value = self.value_get()

        if self.solid is True:
            # Scale value to final size.
            barHeight = int( maxBarSize[1] * ( value / float(100) ) )
            logging.debug("Bar Total Value {:03}, Scaled {}".format(value,barHeight))

            # Calculate bar details Top and Left
            barPosition = barMin
            barSize = (maxBarSize[0] , barHeight)
        else:
            # Line width divided by two
            barY = int( math.ceil( maxBarSize[1] / 60 ) )

            # Recalculate
            barMin = (self.barXYPadding[0],
                      self.barXYPadding[1] + barY )

            # Calculate middle of bar.
            barHeight = int( maxBarSize[1] * ( value / float(100) ) ) - barY

            # To be fair I don't understand why I only add the padding
            # it should be BarMin[1]
            barPosition = ( barMin[0], barHeight + self.barXYPadding[1] )
            barSize = (  maxBarSize[0], barY * 2 )

        # Check for clipping
        bar_colour = self.bar_colour
        if self.value_clipped() is True:
            bar_colour = self.bar_colour_clipped

        # Now draw a box
        pygame.draw.rect(panel, bar_colour, (barPosition , barSize), 0)

        # Flip False means leave the graph upside down.
        if self.flip is False:
            panel = pygame.transform.flip(panel,False,True)
        self.surfaces['panel'].blit(panel,(0,0))

    def _render_overlay(self):
        if self.render_overlay is False:
            return

        # Figure out text size
        textSize = int( math.ceil( self.surfaces['panel'].get_height() / 10.0 ))
        if not hasattr(self, 'overlay_font'):
            # Create a font cache
            self.overlay_font = pygame.font.Font('fonts/destructobeambb_reg.ttf', textSize)

        curValue = self.value_get()
        # Put the text in a Var for later.
        Text = "{:03}".format(curValue)

        lineSize = self.overlay_font.get_linesize()

        if not hasattr(self, 'overlay_cache'):
            self.overlay_cache = dict()

        # Render the text, if it's not cached
        if Text in self.overlay_cache:
            Label = self.overlay_cache[Text]
        else:
            Label = self.overlay_font.render(Text, 1, (255,255,255))
            self.overlay_cache[Text] = Label

        box_size = self.surfaces['panel'].get_size()
        # Blit to overlay
        posMe = ( ( box_size[1] / 2.0 ) - ( Label.get_width() / 2.0 ),
                  box_size[0] - textSize * 2 )

        self.surfaces['panel'].blit(Label,posMe)

    def setBarColour(self,Colour=None):
        if Colour is None:
            return self.barColour
        else:
            self.barColour = Colour

    def setClipColour(self,Colour=None):
        if Colour is None:
            return self.barColourClipped
        else:
            self.barColourClipped = Colour

    def setSolidBar(self,Solid=None):
        if Solid is None:
            return self.solid
        else:
            self.solid = Solid

    def setSidewaysBar(self,Sideways=None):
        if Sideways is None:
            return self.sideways
        else:
            self.sideways = Sideways

    def setFlippedBar(self,Flipped=None):
        if Flipped is None:
            return self.flip
        else:
            self.flip = Flipped

class DialIndicator(commonPanel, SingleIntValue):
    "Dial Graph is a thing apparently"

    def __init__(self, surfaces, panel_spec):
        "Ininitializes a new Dial"
        commonPanel.__init__(self, surfaces, panel_spec)
        SingleIntValue.__init__(self)
        self.arm_colour = (0,255,0)
        if 'arm_colour' in panel_spec:
            self['arm_colour'] = panel_spec['arm_colour']
        self.arm_colour_clipped = (255,0,0)
        if 'arm_colour_clipped' in panel_spec:
            self['arm_colour_clipped'] = panel_spec['arm_colour_clipped']
        self.dial_start = -135
        if 'dial_start' in panel_spec:
            self.dial_start = panel_spec['dial_start']
        self.dial_sweep = 270
        if 'dial_sweep' in panel_spec:
            self.dial_sweep = panel_spec['dial_sweep']
        self.offset_style = False
        if 'offset_style' in panel_spec:
            self.offset_style = panel_spec['offset_style']
        self.sideways = False
        if 'sideways' in panel_spec:
            self.sideways = panel_spec['sideways']
        self.flip = False
        if 'flip' in panel_spec:
            self.flip = panel_spec['flip']

        if self.offset_style is True:
            self.dial_start = -30
            self.dial_sweep = 60

    def _draw_background(self):
        commonPanel._draw_background(self)
        # Try and make a transparent background.
        self.background.fill((0,0,0,0))
        # Draw a background
        box_size = self.background.get_size()
        minWidth = box_size[0]
        if minWidth > box_size[1]:
            minWidth = box_size[1]
        self.radius = int( math.floor( float( minWidth ) / 2 ) ) - 4
        self.circleCentre = (self.radius+3, self.radius+3)

        if self.offset_style is True:
            self.dialCentre = (self.radius+2, int( (self.radius+2) * 0.2))
            self.dialLength = int( float(self.radius) * 1.4 )
        else:
            self.dialCentre = self.circleCentre
            self.dialLength = int( float(self.radius) * 0.9 )

        logging.debug("Setup Centre {}, Radius {}".format(self.circleCentre,self.radius))
        logging.debug("Setup dialCentre {}, dialLength {}".format(self.dialCentre,self.dialLength))

        # Draw the background of the Dial
        pygame.gfxdraw.filled_circle(self.background,
                                     self.circleCentre[0],
                                     self.circleCentre[1],
                                     self.radius,
                                     self.bg_colour)

        # Draw the border thicker as required.
        for i in xrange(self.border_width):
            pygame.gfxdraw.aacircle(self.background,
                                    self.circleCentre[0],
                                    self.circleCentre[1],
                                    self.radius-i,
                                    self.bg_colour)

        dialZeroAngleRad  = math.radians(self.dial_start)
        dialMaxAngleRad  = math.radians(self.dial_start + self.dial_sweep)
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
                               360 + 90 - ( self.dial_start + self.dial_sweep ),
                               360 + 90 - self.dial_start,
                               self.border_colour)

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
                         self.border_colour,
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
                         self.border_colour,
                         dialMaxEndp2,
                         dialMaxEndp1,
                         thickness)


        divisionWidth = (dialMaxAngleRad - dialZeroAngleRad) /10.0
        fSeq = _get_float_range(dialZeroAngleRad,dialMaxAngleRad,divisionWidth)
        # print("Start {}, End {}, Steps {:f}".format(dialZeroAngleRad,dialMaxAngleRad,divisionWidth))
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
                             self.border_colour,
                             dialPicEndp2,
                             dialPicEndp1,
                             thickness)

    def _render(self):
        if not hasattr(self, 'background'):
            self._draw_background()
        panel = self.background.copy()
        # Draw new line
        # print("Rad {} Length {}".format(self.radius,self.dialLength))
        value = self.value_get()
        dialArmColour = self.arm_colour
        if self.value_clipped() is True:
            dialArmColour = self.arm_colour_clipped
        dialAngle  = (( value / float(100) ) * self.dial_sweep ) + self.dial_start
        dialAngleRad  = math.radians(dialAngle)
        deltaX = int( self.dialLength * math.sin(dialAngleRad) )
        deltaY = int( self.dialLength * math.cos(dialAngleRad) )
        dialEnd = ( self.dialCentre[0] + deltaX, self.dialCentre[1] + deltaY )
        pygame.draw.line(panel,
                         dialArmColour,
                         self.dialCentre,
                         dialEnd,
                         2)
        logging.debug("Dial Value {:03}, Angle {}, X,Y {},{}".format(value,dialAngle,deltaX,deltaY))

        # Inverted since it's drawn upside down
        if self.flip is False:
            panel = pygame.transform.flip(panel,False,True)

        # Rotate by 90o if it's supposed to be sideways
        if self.sideways is True:
            panel = pygame.transform.rotate(panel,90)
            panel = pygame.transform.flip(panel,True,False)


        self.surfaces['panel'].blit(panel,(0,0))
        self._render_overlay()

    def _render_overlay(self):
        if self.render_overlay is False:
            return

        # Figure out text size
        text_size = int( math.ceil( self.surfaces['panel'].get_height() / 10.0 ))
        if not hasattr(self, 'overlay_font'):
            # Create a font cache
            self.overlay_font = pygame.font.Font('fonts/destructobeambb_reg.ttf', text_size)

        cur_value = self.value_get()
        # Put the text in a Var for later.
        Text = "{:03}".format(cur_value)

        line_size = self.overlay_font.get_linesize()

        if not hasattr(self, 'overlay_cache'):
            self.overlay_cache = dict()

        # Render the text, if it's not cached
        if Text in self.overlay_cache:
            Label = self.overlay_cache[Text]
        else:
            Label = self.overlay_font.render(Text, 1, (255,255,255))
            self.overlay_cache[Text] = Label

        box_size = self.surfaces['panel'].get_size()
        # Blit to overlay
        posMe = ( ( box_size[1] / 2.0 ) - ( Label.get_width() / 2.0 ),
                  box_size[0] * 2 / 3  )

        # overlay.blit(Label,posMe)

        self.surfaces['panel'].blit(Label,posMe)
