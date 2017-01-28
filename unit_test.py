#!/usr/bin/python

import console80v2

singleton = console80v2.singleIntValue()
print "=== Singleton Time ==="
print ""
print singleton
print ""
print "Set a max number of items in history"
singleton.setMaxHistoryLength(4)
print singleton
print ""
print "Add 0 through 7 to history"
for i in range(1,8):
    singleton.updateValue(i)
print singleton
print "Increase the history length"
singleton.setMaxHistoryLength(5)
print "Add 1 through 19 to history"
for i in range(1,20):
    singleton.updateValue(i)
print singleton
print ""
print "History statistics"
print "Avg: {}".format(singleton.getHistoryAvg())
print "Max: {}".format(singleton.getHistoryMax())
print "Min: {}".format(singleton.getHistoryMin())
print "Last 1: {}".format(singleton.getHistoryLast())
print "Last 3: {}".format(singleton.getHistoryLast(3))
print ""
print "Get current Value"
print "Current: {}".format(singleton.getValue())
print "Scaled: {}".format(singleton.getScaledValue())
print ""
print "Add values outside the range"
singleton.updateValue(101)
print "Get the value back {}".format(singleton.getValue())
print "Get a scaled value back {}".format(singleton.getScaledValue())
print "Am I clipping {}".format(singleton.isClipped())
print ""
singleton.updateValue(-1)
print "Get the value back {}".format(singleton.getValue())
print "Get a scaled value back {}".format(singleton.getScaledValue())
print "Am I clipping {}".format(singleton.isClipped())
print ""
singleton.updateValue(5)
print singleton
print "Get the value back {}".format(singleton.getValue())
print "Am I clipping {}".format(singleton.isClipped())
print ""
print "Set the range 1 - 10"
singleton.setRange((0,10))
print singleton
print ""
print "Sweep to 10 and back"
for i in range(22):
    singleton.sweepValue()
    print singleton
print ""
print ""
coord = console80v2.singleCoordValue()
print "=== Co-Ordinates Time ==="
print ""
print coord
print ""
print "Set a max number of items in history to 4"
coord.setMaxHistoryLength(4)
print coord
print ""
print "Add 0 through 7 to history"
for i in range(1,8):
    coord.updateValue((i**2,i**2))
print coord
print ""
print "Set a max number of items in history to 5"
coord.setMaxHistoryLength(5)
print coord
print ""
print "Add 1 through 19 to history"
for i in range(4,8):
    coord.updateValue((i**2,i**2))
print coord
print ""
print "History statistics"
print "Avg: {}".format(coord.getHistoryAvg())
print "Max: {}".format(coord.getHistoryMax())
print "Min: {}".format(coord.getHistoryMin())
print "Last 1: {}".format(coord.getHistoryLast())
print "Last 3: {}".format(coord.getHistoryLast(3))
print ""
print "Get current Value"
print "Current: {}".format(coord.getValue())
print ""
print "Add values outside the range"
coord.updateValue((101,101))
print "Get the value back {}".format(coord.getValue())
print "Am I clipping {}".format(coord.isClipped())
print ""
coord.updateValue((-1,-1))
print "Get the value back {}".format(coord.getValue())
print "Am I clipping {}".format(coord.isClipped())
print ""
coord.updateValue((0,0))
print "Get the value back {}".format(coord.getValue())
print "Am I clipping {}".format(coord.isClipped())
print ""
print "Set the range -5,-5 - 5,5"
coord.setRange(((-5 , -5) , (5 , 5)))
print coord
print ""
print "Sweep to 5 and back to -5"
for i in range(22):
    coord.sweepValue()
    print coord
print ""



