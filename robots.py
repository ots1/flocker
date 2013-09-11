from SimpleServer import Server, Channel
import numpy as np
from time import sleep
import pygame
import sys
import hashlib
#from lab2rgb import lab2rgb

class PlayerChannel(Channel):
    """This function, and particularly 'handle_data' receives and
    processes the data sent by the client."""
    def __init__(self, *args):
        self.finished_handshake = False
        Channel.__init__(self,*args)

    def handle_data(self, data):
        data = data.splitlines()
        for line in data:
            if not self.finished_handshake:
                print 'Receiving team...', line
                self.player_id = self.server.world.add_player_by_team(line)
                self.finished_handshake = True
                print 'player id is', self.player_id
                #self.Send('Team name accepted. GO!\n')
            else:
                spl_line = line.split()
                if spl_line and (spl_line[0] == 'QUIT'):
                    self.close_when_done()
                elif spl_line and (spl_line[0] == 'ACC'):
                    self.server.world.players[self.player_id].turn['acc'] = \
                        np.array(map(float, spl_line[1:3]))
                    
    def Close(self):
        if self.finished_handshake:
            self.server.world.remove_player(self.player_id)


class GameServer(Server):
    ChannelType = PlayerChannel

    def __init__(self, world, localaddr=None):
        self.world = world
        if localaddr is None:
            Server.__init__(self)
        else:
            Server.__init__(self, localaddr)

    def accept_connection(self, c):
        pass #c.Send("Welcome to the server.")

    def gather_outgoing_data(self):
        for c in self.channels:
            if c.finished_handshake and not c.writable(): # not sure why NOT writable
                c.Send(self.state_to_string(world.players[c.player_id].to_send))
                world.players[c.player_id].to_send = {} # reset buffer

    def pump(self):
        self.gather_outgoing_data()
        Server.pump(self)

    @staticmethod
    def state_to_string(player_state):
        state_string = str(player_state['time']) + '\n' 
        state_string += ' '.join(str(n) for n in player_state['self']['pos']) + ' '
        state_string += ' '.join(str(n) for n in player_state['self']['vel']) + ' '
        state_string += player_state['self']['team'] + '\n'
        for p in player_state['visible']:
            state_string += ' '.join(str(n) for n in p['pos']) + ' '
            state_string += ' '.join(str(n) for n in p['vel']) + ' '
            state_string += p['team'] + '\n'
        state_string += '\n'
        return state_string


class Player:
    def __init__(self, robot):
        self.data = robot
        self.turn = {}
        self.to_send = {}


class World:
    """Container class for the world """
    def __init__(self):
        self.tick = 0
        self.next_player_id = 0
        self.max_player_speed = 0.1
        self.max_player_acc = 0.02
        self.players = {} # dictionary of Player objects (containing the player data, state received from the server and state to send
        self.extent = np.array([100.,100.])

    def add_player(self, robot):
        self.players[self.next_player_id] = Player(robot)
        self.next_player_id += 1
        return self.next_player_id - 1 # return the world id of the current player
    
    def add_player_by_team(self, team_id):
        # Let the world decide on a good place for a new player.
        # Do that here.  (For now just put them all at the origin)
        return self.add_player(Robot(team_id,
                                     self.extent * np.random.rand(2),
                                     0.5 * self.max_player_speed * np.random.rand(2)))

    def remove_player(self, player_id):
        print "deleting player", player_id
        del self.players[player_id]
          
    def send_player_data(self):
        """Send each player information about it's current state and environment"""
        for k, p in self.players.iteritems():
            p.to_send = {'time': self.tick, 'self': p.data.self_dict(), 'visible': [self.players[j].data.others_dict() for j in self.visible(k)]}

    def visible(self, player_id):
        visible = self.players.copy() # copy
        visible.pop(player_id, None)
        return visible # could just return the keys instead

    def update(self):
        # transfer the current player data to the output buffer
        self.send_player_data()

        # update world state based on received player turn
        for k, p in self.players.iteritems():
            p.data.pos += p.data.vel
            # check for world boundaries
            idx = (p.data.pos > world.extent)
            p.data.vel[idx] *= -1.
            p.data.pos[idx] -= p.data.pos[idx] - world.extent[idx]
            idx = (p.data.pos < 0.)
            p.data.vel[idx] *= -1.
            p.data.pos[idx] -= p.data.pos[idx]
            
            # if the player has sent a move and this includes acceleration
            if 'acc' in p.turn:
                # clip acceleration
                acc_sq = np.sum(p.turn['acc']**2)
                if (acc_sq > self.max_player_acc**2):
                    p.turn['acc'] = self.max_player_acc * p.turn['acc'] / np.sqrt(acc_sq)
                p.data.vel += p.turn['acc']
                speed_sq = np.sum(p.data.vel**2)
                # clip speed
                if (speed_sq > self.max_player_speed**2):
                    # can include damage or terrain dependent speed etc here
                    p.data.vel = self.max_player_speed * p.data.vel / np.sqrt(speed_sq)
            
            # reset the player turn data
            p.turn = {}

        self.tick += 1
                

class Robot:
    """Representation of a robot"""
    def __init__(self, team, pos, vel):
        self.team = team
        self.pos = pos
        self.vel = vel

    def self_dict(self):
        """Properties a robot AI is allowed to know about itself"""
        return self.__dict__

    def others_dict(self):
        """Properties another robot can see"""
        return self.__dict__ # keep it simple for the moment


class Display:
    def __init__(self, world, size):
        self.world = world
        self.size = size # display resolution

        # initial values for offset and scale: show everything
        self.init_screen_offset = np.array([5.,5.])
        self.screen_offset = self.init_screen_offset.copy()
        self.init_screen_scale = np.min((self.size - 3.*self.screen_offset)/self.world.extent)
        self.screen_scale = self.init_screen_scale

        self.mousedown = False
        self.zoom_rate = 0.0

        self.screen = pygame.display.set_mode(size, pygame.HWSURFACE | pygame.RESIZABLE | pygame.DOUBLEBUF)
        self.font = pygame.font.SysFont("monospace", 10)
        self.team_colour_lookup = {}

    def write(self, text, col, loc):
        label = self.font.render(text, True, col)
        self.screen.blit(label, loc)

    def refresh(self, **kwargs):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'QUIT'
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mousedown = True
                pygame.mouse.get_rel() # reset any mouse movement
            elif event.type == pygame.MOUSEBUTTONUP:
                self.mousedown = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_EQUALS:
                    self.zoom_rate = 0.04
                elif event.key == pygame.K_MINUS:
                    self.zoom_rate = -0.04
                elif event.key == pygame.K_0:
                    self.zoom_rate = 0.0
                    self.screen_offset = self.init_screen_offset.copy()
                    self.screen_scale = np.min((self.size - 3.*self.screen_offset)/self.world.extent)
                elif event.key == pygame.K_q:
                    pygame.quit()
                    return 'QUIT'
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_EQUALS or event.key == pygame.K_MINUS:
                    self.zoom_rate = 0.0
            elif event.type == pygame.VIDEORESIZE:
                self.size = event.size
                screen=pygame.display.set_mode(event.size,pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE)

        if self.mousedown:
            self.screen_offset += pygame.mouse.get_rel()

        self.screen_scale *= 1. + self.zoom_rate
        # centre scale on the mouse cursor position
        self.screen_offset *= 1. + self.zoom_rate 
        self.screen_offset -= self.zoom_rate * np.array(pygame.mouse.get_pos())

        self.screen.fill((0,0,0))

        # draw the bounding rectangle
        tl = self.world2screen(np.array([0.,0.]))
        br = self.world2screen(self.world.extent)
        boundRect = pygame.Rect((tl[0],tl[1]), (br[0]-tl[0],br[1]-tl[1]))
        pygame.draw.rect(self.screen, (255,255,255), boundRect, 1)

        for k, p in self.world.players.iteritems():
            self.render_robot(p.data)

        self.write(kwargs['info'], (255,255,255), (0,0))
        pygame.display.flip()

    def render_robot(self, robot):
        c1, c2 = self.team_colours(robot.team)

        pygame.draw.line(self.screen, c2,
                         self.world2screen(robot.pos),
                         self.world2screen(robot.pos+10.*robot.vel))

        pygame.draw.circle(self.screen, c2, 
                           self.world2screen(robot.pos),
                           4)
        pygame.draw.circle(self.screen, c1,
                           self.world2screen(robot.pos),
                           2)

    def team_colours(self, team):
        """hash team to two RGB colours"""
        if team in self.team_colour_lookup:
            return self.team_colour_lookup[team]
        
        team_hash = int(hashlib.md5(team).hexdigest(), 16)

        c1 = ((team_hash >> 16) & 0xFF,
              (team_hash >> 8) & 0xFF,
              (team_hash) & 0xFF)
    
        c2 = ((team_hash >> 40) & 0xFF,
              (team_hash >> 32) & 0xFF,
              (team_hash >> 24) & 0xFF)

        self.team_colour_lookup[team] = (c1, c2)
        return (c1, c2)

    def world2screen(self, coords):
        return tuple((self.screen_scale * coords + self.screen_offset).astype(int))


if __name__=='__main__':
    pygame.init()
    world = World()
    server = GameServer(world)
    display = Display(world, (640,480))
    game_clock = pygame.time.Clock()
    
    while 1:
        server.pump()
        world.update()
        status = display.refresh(info="%.2f" % game_clock.get_fps()+" fps")
        if status == 'QUIT':
            # kill the server cleanly...
            sys.exit(0)
        game_clock.tick(60)  # target framerate in fps
