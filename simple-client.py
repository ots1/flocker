import numpy as np
import sys
from time import sleep
from select import select

# simple client
print 'TEST TEAM\n\n'

while 1:
    time = raw_input()
    me = raw_input()
    me = me.split(None, 4)
    mypos = np.array(me[0:2])
    myvel = np.array(me[2:4])
    myteam = me[-1]

    others = []
    other_str = raw_input()
    while other_str:
        other_str = other_str.split(None, 4)
        other = {}
        other['pos'] = np.array(other_str[0:2]).astype(float)
        other['vel'] = np.array(other_str[2:4]).astype(float)
        other['team'] = other_str[-1]
        others.append(other)
        other_str = raw_input()

    sys.stderr.write('got: time =' + str(time) + ', mypos=' + str(mypos) + ', myvel=' + str(myvel) + ', myteam =' + str(myteam) + ', others =' + str(others) + '\n')
    # note - if the client runs slowly for some reason, the input
    # buffer will fill up, and there is no attempt to read the latest
    # data available - it will just respond one at a time to each
    # input, even if this is rather stale information.
    # Several possibilities: don't block in input with threads or select
    # Connect directly to the socket.
