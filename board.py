import pygame
import copy
from pieces import *
import os

class Board:
    images = {}

    def __init__(self):
        self.board = self.create_board()
        self.move_history = []
        self.current_turn = 'white'  # Instance variable, not class variable
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
            piece = self.get_piece(start_row, start_col)
            if not piece:
                return False
            if self.current_turn != piece.color:
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
            return None

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

        return last_move

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
        for end_row, end_col in self.generate_pseudolegal_moves_from_square(row, col):
            if not self.would_be_in_check(piece.color, row, col, end_row, end_col):
                moves.append((end_row, end_col))
        return moves

    def clone(self):
        # Create a deep copy suitable for search, without reusing move history
        new_board = Board()
        new_board.board = [[copy.deepcopy(self.board[r][c]) for c in range(8)] for r in range(8)]
        new_board.current_turn = self.current_turn
        new_board.move_history = []
        return new_board

    def to_fen(self):
        # Piece placement
        rows = []
        for r in range(8):
            fen_row = ''
            empty = 0
            for c in range(8):
                p = self.get_piece(r, c)
                if not p:
                    empty += 1
                else:
                    if empty:
                        fen_row += str(empty)
                        empty = 0
                    ch = {
                        'pawn': 'p', 'knight': 'n', 'bishop': 'b',
                        'rook': 'r', 'queen': 'q', 'king': 'k'
                    }.get(p.name, '?')
                    if p.color == 'white':
                        ch = ch.upper()
                    fen_row += ch
            if empty:
                fen_row += str(empty)
            rows.append(fen_row)
        # FEN is rank 8 to 1, our row 0 is rank 8
        placement = '/'.join(rows)

        # Active color
        active = 'w' if self.current_turn == 'white' else 'b'

        # Castling rights inferred from has_moved flags at start squares
        rights = ''
        wk = self.get_piece(7, 4)
        wr_a = self.get_piece(7, 0)
        wr_h = self.get_piece(7, 7)
        if isinstance(wk, King) and not wk.has_moved:
            if isinstance(wr_h, Rook) and not wr_h.has_moved:
                rights += 'K'
            if isinstance(wr_a, Rook) and not wr_a.has_moved:
                rights += 'Q'
        bk = self.get_piece(0, 4)
        br_a = self.get_piece(0, 0)
        br_h = self.get_piece(0, 7)
        if isinstance(bk, King) and not bk.has_moved:
            if isinstance(br_h, Rook) and not br_h.has_moved:
                rights += 'k'
            if isinstance(br_a, Rook) and not br_a.has_moved:
                rights += 'q'
        if rights == '':
            rights = '-'

        # En passant target square: not tracked (no en passant), use '-'
        ep = '-'

        # Halfmove clock and fullmove number: minimal viable values
        halfmove = '0'
        fullmove = str(1 + len(self.move_history) // 2)

        return f"{placement} {active} {rights} {ep} {halfmove} {fullmove}"

    def generate_pseudolegal_moves(self, color):
        moves = []
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece and piece.color == color:
                    for end_row, end_col in self.generate_pseudolegal_moves_from_square(row, col):
                        moves.append(((row, col), (end_row, end_col)))
        return moves

    def generate_pseudolegal_moves_from_square(self, row, col):
        piece = self.get_piece(row, col)
        if not piece:
            return []

        moves = []
        color = piece.color
        opponent = 'black' if color == 'white' else 'white'

        def add_if_empty_or_capture(r, c):
            if 0 <= r < 8 and 0 <= c < 8:
                target = self.get_piece(r, c)
                if not target or target.color == opponent:
                    moves.append((r, c))

        if isinstance(piece, Pawn):
            direction = -1 if color == 'white' else 1
            start_row = 6 if color == 'white' else 1

            one_ahead_r, one_ahead_c = row + direction, col
            if 0 <= one_ahead_r < 8 and not self.get_piece(one_ahead_r, one_ahead_c):
                moves.append((one_ahead_r, one_ahead_c))
                two_ahead_r = row + 2 * direction
                if row == start_row and not self.get_piece(two_ahead_r, col):
                    moves.append((two_ahead_r, col))

            for dc in (-1, 1):
                tr, tc = row + direction, col + dc
                if 0 <= tr < 8 and 0 <= tc < 8:
                    target = self.get_piece(tr, tc)
                    if target and target.color == opponent:
                        moves.append((tr, tc))
            # En passant not implemented

        elif isinstance(piece, Knight):
            for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
                add_if_empty_or_capture(row + dr, col + dc)

        elif isinstance(piece, Bishop):
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    target = self.get_piece(r, c)
                    if not target:
                        moves.append((r, c))
                    else:
                        if target.color == opponent:
                            moves.append((r, c))
                        break
                    r += dr
                    c += dc

        elif isinstance(piece, Rook):
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    target = self.get_piece(r, c)
                    if not target:
                        moves.append((r, c))
                    else:
                        if target.color == opponent:
                            moves.append((r, c))
                        break
                    r += dr
                    c += dc

        elif isinstance(piece, Queen):
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    target = self.get_piece(r, c)
                    if not target:
                        moves.append((r, c))
                    else:
                        if target.color == opponent:
                            moves.append((r, c))
                        break
                    r += dr
                    c += dc

        elif isinstance(piece, King):
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    add_if_empty_or_capture(row + dr, col + dc)

            # Castling (pseudolegal): squares clear and rook unmoved
            if not piece.has_moved and row in (0, 7):
                # Kingside
                rook = self.get_piece(row, 7)
                if isinstance(rook, Rook) and not rook.has_moved:
                    if not self.get_piece(row, 5) and not self.get_piece(row, 6):
                        # Ensure king doesn't castle out of, through, or into check
                        if not self.is_in_check(color) and \
                           not self.would_be_in_check(color, row, col, row, 5) and \
                           not self.would_be_in_check(color, row, col, row, 6):
                            moves.append((row, 6))
                # Queenside
                rook = self.get_piece(row, 0)
                if isinstance(rook, Rook) and not rook.has_moved:
                    if not self.get_piece(row, 1) and not self.get_piece(row, 2) and not self.get_piece(row, 3):
                        if not self.is_in_check(color) and \
                           not self.would_be_in_check(color, row, col, row, 3) and \
                           not self.would_be_in_check(color, row, col, row, 2):
                            moves.append((row, 2))

        return moves
