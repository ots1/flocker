import pygame, sys
import hashlib


screen_size = (640, 480)
x,y=0,0
vx,vy=3,5

def team_colours(team_name):
    team_hash = int(hashlib.md5(team_name).hexdigest(), 16)
    c1 = ((team_hash >> 16) & 0xFF,
          (team_hash >> 8) & 0xFF,
          (team_hash) & 0xFF)
    
    c2 = ((team_hash >> 40) & 0xFF,
          (team_hash >> 32) & 0xFF,
          (team_hash >> 24) & 0xFF)
          
    return (c1, c2)


if __name__=='__main__':
    pygame.init()
    screen = pygame.display.set_mode(screen_size)

    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
               sys.exit()
        
#        x += vx
#        y += vy
#        if x < 0 or x >= screen_size[0]: vx = -vx
#        if y < 0 or y >= screen_size[1]: vy = -vy

        screen.fill((0,0,0))
        #pygame.draw.circle(screen, (255,0,0), (x,y), 20)
        for i in range(0,10):
            for j in range(0,10):
                cols = team_colours(str(j+10*i))
                pygame.draw.circle(screen, cols[1], (50*j, 50*i), 24)
                pygame.draw.circle(screen, cols[0], (50*j, 50*i), 20)
                
        pygame.display.flip()

