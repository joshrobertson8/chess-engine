import pygame
from game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 800))
    pygame.display.set_caption('Chess Game')

    game = Game(screen)
    game.run()  # Start the game loop

    pygame.quit()

if __name__ == "__main__":
    main()
