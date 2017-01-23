import os
import math
import time
import console80

# Create an instance of the PyScope class
scope = console80.MainScreen(hw=False)
panels = scope.autoLayoutPanels((4,3))
scopePanels = []
for panel in panels:
    print panel
    tgraph = console80.DialIndicator(scope.screen)
    tgraph.setPosition(panel['position'])
    tgraph.setSize(panel['size'])
    tgraph.setValue(45)
    scopePanels.append(tgraph)

clock = scope.createClock()
i = 1
change = 1
while 1:
    for panel in scopePanels:
        clock.tick(180)
        panel.setValue(i)
        panel.Draw()
    scope.redrawScreen()
    if i >= 100 or i < 1:
        change *= -1
        fps = clock.get_fps()
        print "Current FPS is {}".format(fps)
    i += change

time.sleep(10)
exit()

        
