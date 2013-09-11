import numpy as np
import sys
import socket
import asyncore
import asynchat
from time import sleep

class State:
    pass

class GameServerChannel(asynchat.async_chat):
    """The client's representation of the server"""
    message_terminator = '\n\n'
   
    def __init__(self, serveraddr=('localhost', 1234)):
        asynchat.async_chat.__init__(self)
        self.ibuffer = ""
        self.obuffer = []
        self.set_terminator(self.message_terminator)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(serveraddr)
        self.latest_state = None
        self.my_team = None

    def collect_incoming_data(self, data):
        self.ibuffer += data

    def found_terminator(self):
        data = self.ibuffer
        self.ibuffer = ""
        if self.my_team is None:
            # receive the team name as understood by the server
            self.my_team = data
        else:
            self.latest_state = self.parse_data_string(data)
            
    def get_state(self):
        return self.latest_state
        
    def Send(self, data):
        asynchat.async_chat.push(self, data)

    def parse_data_string(self, data):
        state = State()
        data = data.splitlines()
        state.time = data[0]
        posvel = data[1].split()
        state.me = {}
        state.me['pos'] = np.array(posvel[0:2]).astype(float)
        state.me['vel'] = np.array(posvel[2:4]).astype(float)
        state.visible = []
        for line in data[2:]:
            spl_line = line.split(None,4)
            other = {}
            other['pos'] = np.array(spl_line[0:2]).astype(float)
            other['vel'] = np.array(spl_line[2:4]).astype(float)
            other['team'] = np.array(spl_line[-1])
            state.visible.append(other)
        return state
 
    def handle_close(self):
        asynchat.async_chat.handle_close(self)
        print 'Client: connection to server lost.'
        sys.exit(0)

def get_move(state):
    """Calculate the best move somehow."""
    acc = np.zeros(2)
    group_scale = 0.001
    near_distance = 10.0 # when does a boid consider itself too near another?
    near_scale = 0.001
    velocity_scale = 0.01
    
    if state is not None and len(state.visible) > 0:
        # steer towards local average position
        ave_pos = np.mean([a['pos'] for a in state.visible], axis=0)
        acc += group_scale * (ave_pos - state.me['pos'])

        # avoid getting too close
        near_boids = np.array([a['pos'] for a in state.visible if np.sum((a['pos'] - state.me['pos'])**2) < near_distance**2])
        if len(near_boids) > 0:
            r = (np.mean(near_boids) - state.me['pos'])
            acc -= near_scale * r / np.sum(r**2)
    
        # steer towards average heading of group
        ave_vel = np.mean([a['vel'] for a in state.visible], axis=0)
        acc += velocity_scale * (ave_vel - state.me['vel'])

    # add some repulsion from near the edges
    #acc[state.me['pos'] < 10] += 10. - state.me['pos'][state.me['pos']<10]
    #acc[state.me['pos'] > 90] -= 10. - (state.me['pos'][state.me['pos']>90] - 90.)

    # add some random jitter
    acc += 0.01 * (np.random.rand(2) - 0.5)

    return 'ACC ' + ' '.join(str(n) for n in acc) + '\n\n'


if __name__=='__main__':
    g = GameServerChannel()
    g.Send('Team name\n\n')
    tick = None # when was the last update sent?

    while 1:
        sleep(0.01) # Aim for about 60 updates per second to match the frame rate.  Could do this better with pygame.
        # poll for new input
        asyncore.poll()
        # pull the latest state from the server
        state = g.get_state()

        if (not state) or (state.time == tick):
            continue
     
        # calculate the move (might be a while, or very quick)
        g.Send(get_move(state))
        tick = state.time
