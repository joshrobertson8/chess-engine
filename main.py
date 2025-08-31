import pygame
from game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((1100, 800))
    pygame.display.set_caption('Chess Game + Sidebar')

    game = Game(screen)
    game.run()  # Start the game loop

    pygame.quit()

if __name__ == "__main__":
    main()
