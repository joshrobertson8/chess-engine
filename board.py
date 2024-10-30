import pygame
from pieces import *
import os

class Board:
    images = {}
    current_turn = 'white'

    def __init__(self):
        self.board = self.create_board()
        self.move_history = []
        if not Board.images:
            self.load_images()

    def create_board(self):
        board = [[None for _ in range(8)] for _ in range(8)]

        # Place black pieces
        board[0][0] = Rook('black')
        board[0][1] = Knight('black')
        board[0][2] = Bishop('black')
        board[0][3] = Queen('black')
        board[0][4] = King('black')
        board[0][5] = Bishop('black')
        board[0][6] = Knight('black')
        board[0][7] = Rook('black')
        for i in range(8):
            board[1][i] = Pawn('black')

        # Place white pieces
        board[7][0] = Rook('white')
        board[7][1] = Knight('white')
        board[7][2] = Bishop('white')
        board[7][3] = Queen('white')
        board[7][4] = King('white')
        board[7][5] = Bishop('white')
        board[7][6] = Knight('white')
        board[7][7] = Rook('white')
        for i in range(8):
            board[6][i] = Pawn('white')

        return board

    def load_images(self):
        pieces = ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']
        colors = ['white', 'black']
        for color in colors:
            for piece in pieces:
                image_path = os.path.join('assets', f"{color}_{piece}.png")
                if os.path.exists(image_path):
                    image = pygame.image.load(image_path)
                    Board.images[f"{color}_{piece}"] = pygame.transform.scale(image, (100, 100))

    def draw(self, screen):
        colors = [(255, 206, 158), (209, 139, 71)]
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                pygame.draw.rect(screen, color, pygame.Rect(col * 100, row * 100, 100, 100))
                piece = self.board[row][col]
                if piece:
                    image = Board.images.get(f"{piece.color}_{piece.name}")
                    if image:
                        screen.blit(image, (col * 100, row * 100))

    def get_piece(self, row, col):
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None

    def is_empty(self, row, col):
        return self.get_piece(row, col) is None

    def make_move(self, start_row, start_col, end_row, end_col, switch_turn=True, validate=True):
        if validate:
            if self.current_turn != self.get_piece(start_row, start_col).color:
                return False

            if not (0 <= end_row < 8 and 0 <= end_col < 8):
                return False

            piece = self.board[start_row][start_col]
            target_piece = self.board[end_row][end_col]

            if target_piece and target_piece.name == 'king':
                return False

            if piece and piece.is_valid_move(start_row, start_col, end_row, end_col, self):
                if target_piece and target_piece.color == piece.color:
                    return False

                if self.would_be_in_check(self.current_turn, start_row, start_col, end_row, end_col):
                    return False
            else:
                return False

        piece = self.board[start_row][start_col]
        target_piece = self.board[end_row][end_col]

        move_details = {
            'piece': piece,
            'captured_piece': target_piece,
            'castling': False,
            'en_passant': False,
            'promotion': False,
            'rook_move': None,
            'start_pos': (start_row, start_col),
            'end_pos': (end_row, end_col),
            'piece_has_moved_before_move': getattr(piece, 'has_moved', False)
        }

        if isinstance(piece, King) and abs(end_col - start_col) == 2:
            move_details['castling'] = True
            if end_col == 6:
                rook = self.get_piece(start_row, 7)
                if rook and isinstance(rook, Rook) and not rook.has_moved:
                    self.board[start_row][5] = rook
                    self.board[start_row][7] = None
                    move_details['rook_move'] = {
                        'rook': rook,
                        'start_pos': (start_row, 7),
                        'end_pos': (start_row, 5),
                        'rook_has_moved_before_move': rook.has_moved
                    }
                    rook.has_moved = True
            elif end_col == 2:
                rook = self.get_piece(start_row, 0)
                if rook and isinstance(rook, Rook) and not rook.has_moved:
                    self.board[start_row][3] = rook
                    self.board[start_row][0] = None
                    move_details['rook_move'] = {
                        'rook': rook,
                        'start_pos': (start_row, 0),
                        'end_pos': (start_row, 3),
                        'rook_has_moved_before_move': rook.has_moved
                    }
                    rook.has_moved = True

        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = None
        piece.has_moved = True

        if isinstance(piece, Pawn):
            if (piece.color == 'white' and end_row == 0) or (piece.color == 'black' and end_row == 7):
                self.promote_pawn(piece, end_row, end_col)
                move_details['promotion'] = True

        self.move_history.append(move_details)

        if switch_turn:
            self.current_turn = 'black' if self.current_turn == 'white' else 'white'

        return True

    def unmake_move(self, switch_turn=True):
        if not self.move_history:
            return False

        last_move = self.move_history.pop()
        piece = last_move['piece']
        captured_piece = last_move['captured_piece']
        start_row, start_col = last_move['start_pos']
        end_row, end_col = last_move['end_pos']
        piece_has_moved_before_move = last_move['piece_has_moved_before_move']

        self.board[start_row][start_col] = piece
        self.board[end_row][end_col] = captured_piece
        piece.has_moved = piece_has_moved_before_move

        if last_move['castling'] and last_move['rook_move']:
            rook = last_move['rook_move']['rook']
            rook_start_row, rook_start_col = last_move['rook_move']['start_pos']
            rook_end_row, rook_end_col = last_move['rook_move']['end_pos']
            rook_has_moved_before_move = last_move['rook_move']['rook_has_moved_before_move']
            self.board[rook_start_row][rook_start_col] = rook
            self.board[rook_end_row][rook_end_col] = None
            rook.has_moved = rook_has_moved_before_move

        if last_move['promotion']:
            self.board[start_row][start_col] = Pawn(piece.color)

        if switch_turn:
            self.current_turn = 'black' if self.current_turn == 'white' else 'white'

        return True

    def promote_pawn(self, pawn, row, col):
        self.board[row][col] = Queen(pawn.color)

    def is_in_check(self, color):
        king_position = None
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece and piece.color == color and piece.name == 'king':
                    king_position = (row, col)
                    break
            if king_position:
                break
        if not king_position:
            return True

        opponent_color = 'black' if color == 'white' else 'white'
        for row, col, piece in self.get_all_pieces(opponent_color):
            if piece.is_valid_move(row, col, king_position[0], king_position[1], self):
                return True
        return False

    def is_checkmate(self, color):
        if not self.is_in_check(color):
            return False

        for row, col, piece in self.get_all_pieces(color):
            for move in self.get_valid_moves(piece, row, col):
                self.make_move(row, col, move[0], move[1], switch_turn=False, validate=False)
                if not self.is_in_check(color):
                    self.unmake_move(switch_turn=False)
                    return False
                self.unmake_move(switch_turn=False)
        return True

    def is_stalemate(self, color):
        if self.current_turn != color:
            return False

        if self.is_in_check(color):
            return False

        for row, col, piece in self.get_all_pieces(color):
            for move in self.get_valid_moves(piece, row, col):
                self.make_move(row, col, move[0], move[1], switch_turn=False, validate=False)
                self.unmake_move(switch_turn=False)
                return False
        return True

    def is_game_over(self):
        return (self.is_checkmate('white') or self.is_checkmate('black') or
                self.is_stalemate('white') or self.is_stalemate('black'))

    def get_all_pieces(self, color=None):
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece and (color is None or piece.color == color):
                    pieces.append((row, col, piece))
        return pieces

    def would_be_in_check(self, color, start_row, start_col, end_row, end_col):
        self.make_move(start_row, start_col, end_row, end_col, switch_turn=False, validate=False)
        in_check = self.is_in_check(color)
        self.unmake_move(switch_turn=False)
        return in_check

    def get_valid_moves(self, piece, row, col):
        moves = []
        for end_row in range(8):
            for end_col in range(8):
                if piece.is_valid_move(row, col, end_row, end_col, self):
                    if not self.would_be_in_check(piece.color, row, col, end_row, end_col):
                        moves.append((end_row, end_col))
        return moves
