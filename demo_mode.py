import os
import math
import time
import console80
import random

# Create an instance of the PyScope class
scope = console80.MainScreen(hw=True)
Tick = 60
panels = scope.autoLayoutPanels((10,10),label=0.1)
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
            solid=True
            if panel['rpos'][1] % 4 > 0:
                solid=False
            gPanel.addBar(Solid=solid,Sideways=False,Flip=False)
            gPanel.dial.setValue(random.randint(0, 100))
            gPanel.setName("Bar Graph {}".format(panel['rpos']) )
        
    gPanel.setLabelText( " {} ".format(gPanel.getName()) )
    scopePanels.append(gPanel)

clock = scope.createClock()

average = []
counter = 1
overlay = True
while 1:
    counter += 1
    for panel in scopePanels:
        panel.dial.setRandValue()
        panel.dial.renderOverlay(overlay)
        
    scope.redrawScreen()
    clock.tick(Tick)
    if counter % 100 is 0:
        fps = clock.get_fps()
        average.append(fps)
        running = sum(average) / float(len(average))
    if counter % 1000 is 0:
        print 'Current FPS is {:3.2f} running average {:3.2f}'.format(fps,running)
        if overlay is True: 
            overlay = False
        else:
            overlay = True


exit()

        
