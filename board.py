# board.py

import pygame
from pieces import *
import os
import copy

class Board:
    images = {}
    current_turn = 'white'  # Tracks whose turn it is

    def __init__(self):
        self.board = self.create_board()
        self.move_history = []  # Stack to keep track of moves for unmake_move
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
                else:
                    print(f"Image not found: {image_path}")

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
                    else:
                        print(f"Image not loaded for {piece.color} {piece.name}")

    def get_piece(self, row, col):
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None

    def make_move(self, start_row, start_col, end_row, end_col):
        print(f"Attempting to make move from ({start_row}, {start_col}) to ({end_row}, {end_col})")
        
        if self.current_turn != self.get_piece(start_row, start_col).color:
            print(f"It's not {self.get_piece(start_row, start_col).color}'s turn.")
            return False  # Not the player's turn

        if not (0 <= end_row < 8 and 0 <= end_col < 8):
            print("Move is out of bounds.")
            return False  # Move is out of bounds
        
        piece = self.board[start_row][start_col]
        target_piece = self.board[end_row][end_col]
        
        # Prevent capturing the king
        if target_piece and target_piece.name == 'king':
            print("Attempted to capture the king, which is illegal.")
            return False
        
        if piece and piece.is_valid_move(start_row, start_col, end_row, end_col, self):
            if target_piece and target_piece.color == piece.color:
                print("Cannot capture your own piece.")
                return False  # Can't capture own pieces
            
            # Handle special moves
            move_details = {
                'piece': piece,
                'captured_piece': target_piece,
                'castling': False,
                'en_passant': False,  # Placeholder for future implementation
                'promotion': False,
                'rook_move': None,
                'start_pos': (start_row, start_col),
                'end_pos': (end_row, end_col),
                'piece_has_moved_before_move': piece.has_moved
            }
            
            # Castling
            if isinstance(piece, King) and abs(end_col - start_col) == 2:
                move_details['castling'] = True
                print("Castling move detected.")
                if end_col == 6:  # King-side castling
                    rook = self.get_piece(start_row, 7)
                    if rook and isinstance(rook, Rook) and not rook.has_moved:
                        self.board[start_row][5] = rook
                        self.board[start_row][7] = None
                        rook.has_moved = True
                        move_details['rook_move'] = {
                            'rook': rook,
                            'start_pos': (start_row, 7),
                            'end_pos': (start_row, 5),
                            'rook_has_moved_before_move': rook.has_moved
                        }
                        print("King-side castling performed.")
                elif end_col == 2:  # Queen-side castling
                    rook = self.get_piece(start_row, 0)
                    if rook and isinstance(rook, Rook) and not rook.has_moved:
                        self.board[start_row][3] = rook
                        self.board[start_row][0] = None
                        rook.has_moved = True
                        move_details['rook_move'] = {
                            'rook': rook,
                            'start_pos': (start_row, 0),
                            'end_pos': (start_row, 3),
                            'rook_has_moved_before_move': rook.has_moved
                        }
                        print("Queen-side castling performed.")
            
            # En Passant (Placeholder)
            # TODO: Implement en passant logic if desired
            
            # Make the move
            self.board[end_row][end_col] = piece
            self.board[start_row][start_col] = None
            piece.has_moved = True
            print(f"Moved {piece.color} {piece.name} to ({end_row}, {end_col}).")
            
            # Pawn Promotion
            if isinstance(piece, Pawn):
                if (piece.color == 'white' and end_row == 0) or (piece.color == 'black' and end_row == 7):
                    self.promote_pawn(piece, end_row, end_col)
                    move_details['promotion'] = True
                    print(f"Pawn promotion occurred at ({end_row}, {end_col}).")
            
            # Record the move in history
            self.move_history.append(move_details)
            print(f"Move recorded: {move_details}")
            
            # Switch turn
            self.current_turn = 'black' if self.current_turn == 'white' else 'white'
            print(f"Turn switched to {self.current_turn}.")
            
            return True
        print("Move is invalid.")
        return False

    def unmake_move(self):
        if not self.move_history:
            print("No moves to unmake.")
            return False

        last_move = self.move_history.pop()
        piece = last_move['piece']
        captured_piece = last_move['captured_piece']
        start_row, start_col = last_move['start_pos']
        end_row, end_col = last_move['end_pos']
        piece_has_moved_before_move = last_move['piece_has_moved_before_move']

        print(f"Unmaking move from ({start_row}, {start_col}) to ({end_row}, {end_col})")

        # Reverse the move
        self.board[start_row][start_col] = piece
        self.board[end_row][end_col] = captured_piece
        piece.has_moved = piece_has_moved_before_move
        print(f"Moved {piece.color} {piece.name} back to ({start_row}, {start_col}).")
        
        # Reverse castling
        if last_move['castling'] and last_move['rook_move']:
            rook = last_move['rook_move']['rook']
            rook_start_row, rook_start_col = last_move['rook_move']['start_pos']
            rook_end_row, rook_end_col = last_move['rook_move']['end_pos']
            rook_has_moved_before_move = last_move['rook_move']['rook_has_moved_before_move']
            
            # Move the rook back to its original position
            self.board[rook_start_row][rook_start_col] = rook
            self.board[rook_end_row][rook_end_col] = None
            rook.has_moved = rook_has_moved_before_move
            print(f"Rook moved back from ({rook_end_row}, {rook_end_col}) to ({rook_start_row}, {rook_start_col}).")
        
        # Reverse promotion
        if last_move['promotion']:
            self.board[start_row][start_col] = Pawn(piece.color)
            print(f"Reverted promotion at ({start_row}, {start_col}) to Pawn.")
        
        # Switch turn back
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        print(f"Turn reverted to {self.current_turn}.")

        return True

    def promote_pawn(self, pawn, row, col):
        print(f"{pawn.color.capitalize()} pawn promoted to queen at ({row}, {col})")
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
            print(f"Error: {color} king not found on the board.")
            return True  # Treat missing king as being in check

        opponent_color = 'black' if color == 'white' else 'white'
        for row, col, piece in self.get_all_pieces(opponent_color):
            if piece.is_valid_move(row, col, king_position[0], king_position[1], self):
                print(f"{color} is in check by {piece.color} {piece.name} at ({row}, {col})")
                return True
        return False


    def is_checkmate(self, color):
        print(f"Checking for checkmate for {color}...")
        if not self.is_in_check(color):
            print(f"{color} is not in checkmate because they are not in check.")
            return False

        for row, col, piece in self.get_all_pieces(color):
            for end_row in range(8):
                for end_col in range(8):
                    if piece.is_valid_move(row, col, end_row, end_col, self):
                        if self.make_move(row, col, end_row, end_col):
                            if not self.is_in_check(color):
                                self.unmake_move()
                                print(f"{color} is not in checkmate because move from ({row}, {col}) to ({end_row}, {end_col}) resolves check.")
                                return False
                            self.unmake_move()
        print(f"{color} is in checkmate.")
        return True

    def is_stalemate(self, color):
        print(f"Checking for stalemate for {color}...")
        if self.is_in_check(color):
            print(f"{color} is in check, so no stalemate.")
            return False

        for row, col, piece in self.get_all_pieces(color):
            for end_row in range(8):
                for end_col in range(8):
                    if piece.is_valid_move(row, col, end_row, end_col, self):
                        if self.make_move(row, col, end_row, end_col):
                            if not self.is_in_check(color):
                                self.unmake_move()
                                print(f"{color} is not in stalemate because move from ({row}, {col}) to ({end_row}, {end_col}) is possible.")
                                return False
                            self.unmake_move()
        print(f"{color} is in stalemate.")
        return True

    def is_game_over(self):
        return (self.is_checkmate('white') or self.is_checkmate('black') or
                self.is_stalemate('white') or self.is_stalemate('black'))

    def get_all_pieces(self, color):
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece and piece.color == color:
                    pieces.append((row, col, piece))
        return pieces

    def would_be_in_check(self, color, start_row, start_col, end_row, end_col):
        temp_board = copy.deepcopy(self)
        temp_board.make_move(start_row, start_col, end_row, end_col)
        return temp_board.is_in_check(color)
