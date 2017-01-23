import os
import math
import time
import console80
import random

# Create an instance of the PyScope class
scope = console80.MainScreen(hw=True)
Tick = 0
panels = scope.autoLayoutPanels((2,2),label=0.1)
scopePanels = []
for panel in panels:
    # print panel
    gPanel = console80.GenericPanel(scope.wScreen,panel['rect'],0.1)
    gPanel.setName("Graph {}".format(panel['rpos']) )
    if panel['rpos'][0] % 2 > 0:
        if panel['rpos'][1] % 2 > 0:
            gPanel.addDial(offsetStyle=True)
            gPanel.setName("Offset Dial {}".format(panel['rpos']) )
        else:
            gPanel.addDial(offsetStyle=False)
            gPanel.setName("Normal Dial {}".format(panel['rpos']) )
        # Seed a random value
        gPanel.dial.setValue(random.randint(0, 100))
    else:
        if panel['rpos'][1] % 2 > 0:
            gPanel.addScatter()
            gPanel.dial.setValue((random.randint(0, 100),random.randint(0, 100)))
            gPanel.setName("Scatter Graph {}".format(panel['rpos']) )
        else:
            gPanel.addBar()
            gPanel.dial.setValue(random.randint(0, 100))
            gPanel.setName("Bar Graph {}".format(panel['rpos']) )
        
    gPanel.setLabelText( " {} ".format(gPanel.getName()) )
    scopePanels.append(gPanel)

clock = scope.createClock()

average = []
i = 1
change = 1
while 1:
    for panel in scopePanels:
        panel.dial.setRandValue()

    scope.redrawScreen()
    clock.tick(Tick)
    if i >= 100 or i < 1:
        change *= -1
        fps = clock.get_fps()
        average.append(fps)
        running = sum(average) / float(len(average))
        print "Current FPS is {:3.2f} running average {:3.2f}".format(fps,running)

    i += change


exit()

        
