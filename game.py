# Example file showing a circle moving on self.screen
import pygame
from scripts.entities import PhysicsEntity

class Game:
    def __init__(self):
        # pygame setup
        pygame.display.set_caption('game')
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))
        self.clock = pygame.time.Clock()

        self.movement = [False, False]
        self.player = PhysicsEntity(self, 'player', (50, 50), (8, 15))
        
    def run(self):
        while True:
            # fill the self.screen with a color to wipe away anything from last frame
            self.screen.fill("purple")
            
            self.player.update(self.display, (self.movement[1] - self.movement[0], 0))
            self.player.render(self.display)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        self.player.velocity[1] = -3
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False

                self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
                pygame.display.update()
                self.clock.tick(144) # limit to 60 FPS

if __name__ == "__main__":
    game = Game()
    game.run()