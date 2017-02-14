#!/usr/bin/python

import os
import math
import time
import console80v2
import random

# Create an instance of the PyScope class
scope = console80v2.MainScreen(hw=False)
Tick = 60
panels = scope.auto_layout_panels((1,1),label=0.1)
scopePanels = []
for panel in panels:
    panel['type'] = 'point'
    panel['render_overlay'] = True
    panel['offset_style'] = True
    panel['solid'] = True
    panel['label_text'] = "Graph {}".format(panel['rpos'])
    if panel['rpos'][1] % 2 > 0:
        panel['sideways'] = True
        panel['label_text'] += ' S:T'
    else:
        panel['sideways'] = False
        panel['label_text'] += ' S:F'

    if panel['rpos'][0] % 2 > 0:
        panel['flip'] = True
        panel['label_text'] += ' F:T'
    else:
        panel['flip'] = False
        panel['label_text'] += ' F:F'

    panel_inst = scope.add_panel(panel)
    panel_inst.value_rand()
    scopePanels.append(panel_inst)
clock = scope.create_clock()

average = []
counter = 1
#overlay = True
while 1:
    counter += 1
    for panel in scopePanels:
        panel.value_sweep()
#        panel.dial.renderOverlay(overlay)
    scope.redraw_screen()
    clock.tick(Tick)
    if counter % 100 is 0:
        fps = clock.get_fps()
        average.append(fps)
        running = sum(average) / float(len(average))
        print('Current FPS is {:3.2f} running average {:3.2f}'.format(fps,running))
    if counter % 1000 is 0:
        print('Current FPS is {:3.2f} running average {:3.2f}'.format(fps,running))



exit()
