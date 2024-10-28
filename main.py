# main.py

import pygame
from game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 800))
    pygame.display.set_caption("Chess Game")
    clock = pygame.time.Clock()

    game = Game(screen)

    while True:
        clock.tick(60)  # Limit to 60 FPS
        game.handle_events()
        game.update()
        game.draw()
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
