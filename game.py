# game.py
import pygame
from board import Board
from ai import AI

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.board = Board()
        self.selected_piece = None
        self.font = pygame.font.SysFont(None, 36)
        self.ai = AI('black')  # AI always plays as black with hard difficulty
        self.game_over = False
        self.winner = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if not self.game_over and self.board.current_turn == 'white':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    row, col = pos[1] // 100, pos[0] // 100
                    print(f"User clicked on ({row}, {col})")
                    if self.selected_piece is None:
                        piece = self.board.get_piece(row, col)
                        if piece and piece.color == 'white':
                            self.selected_piece = (row, col, piece)
                            print(f"Selected {piece.color} {piece.name} at ({row}, {col})")
                    else:
                        start_row, start_col, piece = self.selected_piece
                        print(f"Attempting to move {piece.color} {piece.name} from ({start_row}, {start_col}) to ({row}, {col})")
                        if (start_row, start_col) != (row, col):
                            move_successful = self.board.make_move(start_row, start_col, row, col)
                            if move_successful:
                                print(f"Move successful: {piece.color} {piece.name} moved to ({row}, {col})")
                                self.check_game_over()
                            else:
                                print("Move failed. Invalid move.")
                                # Optional: Provide feedback to the player
                        else:
                            print("Clicked on the same square. Deselecting piece.")
                        self.selected_piece = None

    def update(self):
        if not self.game_over and self.board.current_turn == 'black':
            print("AI's turn.")
            move = self.ai.get_move(self.board)
            if move:
                start_pos, end_pos = move
                print(f"AI attempting to move from {start_pos} to {end_pos}")
                if self.board.make_move(*start_pos, *end_pos):
                    print(f"AI moved from {start_pos} to {end_pos}")
                    self.check_game_over()
                else:
                    print("AI attempted an invalid move.")
            else:
                print("AI has no valid moves. Game over.")
                self.game_over = True
                self.winner = 'White'

    def draw(self):
        self.board.draw(self.screen)
        if self.selected_piece:
            row, col, _ = self.selected_piece
            pygame.draw.rect(self.screen, (255, 255, 0), (col * 100, row * 100, 100, 100), 5)
        if self.game_over:
            if self.winner == 'Draw':
                text = self.font.render("Game is a Draw!", True, (255, 255, 0))
            else:
                text = self.font.render(f"{self.winner} wins!", True, (255, 0, 0))
            self.screen.blit(text, (350, 375))
        pygame.display.flip()

    def check_game_over(self):
        print("Checking if the game is over...")
        if self.board.is_checkmate('black'):
            self.game_over = True
            self.winner = 'White'
            print("Checkmate detected. White wins!")
        elif self.board.is_checkmate('white'):
            self.game_over = True
            self.winner = 'Black'
            print("Checkmate detected. Black wins!")
        elif self.board.is_stalemate('black') or self.board.is_stalemate('white'):
            self.game_over = True
            self.winner = 'Draw'
            print("Stalemate detected. The game is a draw.")

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
