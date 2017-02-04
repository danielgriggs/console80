import os
import math
import time
import console80v2
import random

# Create an instance of the PyScope class
scope = console80v2.MainScreen(hw=True)
Tick = 60
panels = scope.autoLayoutPanels((2,2),label=0.1)
scopePanels = []
for panel in panels:
    # print panel
    gPanel = console80v2.GenericPanel(scope.wScreen,panel['rect'],0.1)
    gPanel.setName("Graph {}".format(panel['rpos']) )
    if panel['rpos'][0] % 2 > 0:
        if panel['rpos'][1] % 2 > 0:
            gPanel.addBar(Solid=False,Sideways=False,Flip=True)
            gPanel.dial.setValue(random.randint(0, 100))
            gPanel.setName("Bar Graph {}".format(panel['rpos']) )
        else:
            gPanel.addBar(Solid=False,Sideways=False,Flip=False)
            gPanel.dial.setValue(random.randint(0, 100))
            gPanel.setName("Bar Graph {}".format(panel['rpos']) )

    else:
        if panel['rpos'][1] % 2 > 0:
            gPanel.addBar(Solid=False,Sideways=True,Flip=True)
            gPanel.dial.setValue(random.randint(0, 100))
            gPanel.setName("Bar Graph {}".format(panel['rpos']) )
        else:
            gPanel.addBar(Solid=False,Sideways=True,Flip=False)
            gPanel.dial.setValue(random.randint(0, 100))
            gPanel.setName("Bar Graph {}".format(panel['rpos']) )
        
    gPanel.dial.setValue(random.randint(0, 100))
    gPanel.setLabelText( " {} ".format(gPanel.getName()) )
    gPanel.dial.renderOverlay(True)
    scopePanels.append(gPanel)

clock = scope.createClock()

print "Bouceing at 100"
for j in range(0,3):
    for i in range(97,101):
        time.sleep(1)
        for panel in scopePanels:
            panel.dial.setValue(i)
        time.sleep(0.5)

print "Bouceing at 0"
for j in range(0,5):
    for i in range(3,-1,-1):
        time.sleep(1)
        for panel in scopePanels:
            panel.dial.setValue(i)
        time.sleep(0.5)

print "Running a sweep"
for j in range(0,5):
    for i in range(0,101):
        for panel in scopePanels:
            panel.dial.setValue(i)
        time.sleep(30/100.0)
    for i in range(100,-1,-1):
        for panel in scopePanels:
            panel.dial.setValue(i)
        time.sleep(30/100.0)

print "Finished"

average = []
counter = 1
overlay = True
while 1:
    counter += 1
    for panel in scopePanels:
        panel.dial.setRandValue()

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

        
