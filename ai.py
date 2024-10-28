# ai.py

import random
import time
from pieces import King, Rook, Queen, Bishop, Knight, Pawn

class AI:
    def __init__(self, difficulty, color):
        self.difficulty = difficulty
        self.color = color
        self.opponent_color = 'black' if color == 'white' else 'white'
        self.depth = {'easy': 2, 'medium': 3, 'hard': 4}[difficulty]
        self.piece_square_tables = self.initialize_piece_square_tables()
        self.transposition_table = {}
        self.position_history = {}
        self.zobrist_keys = self.initialize_zobrist_keys()

    def initialize_piece_square_tables(self):
        piece_square_tables = {
            'pawn': [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [5, 10, 10, -20, -20, 10, 10, 5],
                [5, -5, -10, 0, 0, -10, -5, 5],
                [0, 0, 0, 20, 20, 0, 0, 0],
                [5, 5, 10, 25, 25, 10, 5, 5],
                [10, 10, 20, 30, 30, 20, 10, 10],
                [50, 50, 50, 50, 50, 50, 50, 50],
                [0, 0, 0, 0, 0, 0, 0, 0]
            ],
            'queen': [
                [-20, -10, -10, -5, -5, -10, -10, -20],
                [-10, 0, 0, 0, 0, 0, 0, -10],
                [-10, 0, 5, 5, 5, 5, 0, -10],
                [-5, 0, 5, 5, 5, 5, 0, -5],
                [0, 0, 5, 5, 5, 5, 0, -5],
                [-10, 5, 5, 5, 5, 5, 0, -10],
                [-10, 0, 5, 0, 0, 0, 0, -10],
                [-20, -10, -10, -5, -5, -10, -10, -20]
            ],
            'knight': [
                [-50, -40, -30, -30, -30, -30, -40, -50],
                [-40, -20, 0, 5, 5, 0, -20, -40],
                [-30, 5, 10, 15, 15, 10, 5, -30],
                [-30, 0, 15, 20, 20, 15, 0, -30],
                [-30, 5, 15, 20, 20, 15, 5, -30],
                [-30, 0, 10, 15, 15, 10, 0, -30],
                [-40, -20, 0, 0, 0, 0, -20, -40],
                [-50, -40, -30, -30, -30, -30, -40, -50]
            ],
            'bishop': [
                [-20, -10, -10, -10, -10, -10, -10, -20],
                [-10, 5, 0, 0, 0, 0, 5, -10],
                [-10, 10, 10, 10, 10, 10, 10, -10],
                [-10, 0, 10, 10, 10, 10, 0, -10],
                [-10, 5, 5, 10, 10, 5, 5, -10],
                [-10, 0, 5, 10, 10, 5, 0, -10],
                [-10, 0, 0, 0, 0, 0, 0, -10],
                [-20, -10, -10, -10, -10, -10, -10, -20]
            ],
            'rook': [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [5, 10, 10, 10, 10, 10, 10, 5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [0, 0, 0, 5, 5, 0, 0, 0]
            ],
            'king': [
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-20, -30, -30, -40, -40, -30, -30, -20],
                [-10, -20, -20, -20, -20, -20, -20, -10],
                [20, 20, 0, 0, 0, 0, 20, 20],
                [20, 30, 10, 0, 0, 10, 30, 20]
            ]
        }
        return piece_square_tables

    def initialize_zobrist_keys(self):
        import random
        random.seed(0)  # For reproducibility
        zobrist = {}
        pieces = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
        colors = ['white', 'black']
        for piece in pieces:
            for color in colors:
                for square in range(64):
                    zobrist[(piece, color, square)] = random.getrandbits(64)
        zobrist['white_to_move'] = random.getrandbits(64)
        return zobrist

    def get_move(self, board):
        print(f"AI ({self.color}) is calculating move...")
        moves = self.get_all_moves(board, self.color)
        if not moves:
            print(f"AI ({self.color}) has no moves to play.")
            return None

        best_score = float('-inf')
        best_move = None
        alpha = float('-inf')
        beta = float('inf')

        start_time = time.time()

        for move in self.order_moves(moves, board):
            board.make_move(*move[0], *move[1])
            score = self.alpha_beta(board, self.depth - 1, alpha, beta, False)
            board.unmake_move()
            print(f"Evaluated move {move} with score {score}")
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if beta <= alpha:
                print("Alpha-Beta pruning activated.")
                break  # Alpha-Beta pruning

        print(f"AI decision time: {time.time() - start_time:.4f} seconds")
        if best_move:
            print(f"AI ({self.color}) selects move from {best_move[0]} to {best_move[1]} with score {best_score}")
        else:
            print(f"AI ({self.color}) could not find a valid move.")

        return best_move

    def alpha_beta(self, board, depth, alpha, beta, is_maximizing):
        board_hash = self.hash_board(board)
        if board_hash in self.transposition_table:
            print(f"Transposition table hit for hash {board_hash} with score {self.transposition_table[board_hash]}")
            return self.transposition_table[board_hash]

        if depth == 0 or board.is_game_over():
            eval_score = self.evaluate_board(board)
            print(f"Depth {depth}: Evaluated board with score {eval_score}")
            return eval_score

        if is_maximizing:
            max_eval = float('-inf')
            for move in self.order_moves(self.get_all_moves(board, self.color), board):
                board.make_move(*move[0], *move[1])
                eval = self.alpha_beta(board, depth - 1, alpha, beta, False)
                board.unmake_move()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    print("Alpha-Beta pruning activated in maximizing player.")
                    break  # Alpha-Beta pruning
            self.transposition_table[board_hash] = max_eval
            return max_eval
        else:
            min_eval = float('inf')
            for move in self.order_moves(self.get_all_moves(board, self.opponent_color), board):
                board.make_move(*move[0], *move[1])
                eval = self.alpha_beta(board, depth - 1, alpha, beta, True)
                board.unmake_move()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    print("Alpha-Beta pruning activated in minimizing player.")
                    break  # Alpha-Beta pruning
            self.transposition_table[board_hash] = min_eval
            return min_eval

    def hash_board(self, board):
        h = 0
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece:
                    square = row * 8 + col
                    h ^= self.zobrist_keys.get((piece.name, piece.color, square), 0)
        if board.current_turn == 'white':
            h ^= self.zobrist_keys['white_to_move']
        return h

    def get_all_moves(self, board, color):
        moves = []
        for row, col, piece in board.get_all_pieces(color):
            for end_row in range(8):
                for end_col in range(8):
                    if piece.is_valid_move(row, col, end_row, end_col, board):
                        target_piece = board.get_piece(end_row, end_col)
                        if not target_piece or target_piece.color != color:
                            moves.append(((row, col), (end_row, end_col)))
        return moves

    def order_moves(self, moves, board):
        # Order moves to improve alpha-beta pruning efficiency
        def move_score(move):
            start, end = move
            target = board.get_piece(*end)
            score = 0
            if target:
                score += self.evaluate_piece_value(target)  # Capture moves have higher scores
            # Prefer moves by higher value pieces
            piece = board.get_piece(*start)
            piece_order = {'queen': 6, 'rook': 5, 'bishop': 3, 'knight': 3, 'pawn': 1, 'king': 10}
            score += piece_order.get(piece.name, 0)
            return score

        return sorted(moves, key=move_score, reverse=True)

    def evaluate_move(self, board, move):
        piece = board.get_piece(*move[1])
        if piece:
            return self.evaluate_piece_value(piece)
        return 0

    def evaluate_board(self, board):
        piece_value = {
            'pawn': 100,
            'knight': 320,
            'bishop': 330,
            'rook': 500,
            'queen': 900,
            'king': 20000
        }

        total = 0
        for row_index, row in enumerate(board.board):
            for col_index, piece in enumerate(row):
                if piece:
                    value = piece_value.get(piece.name, 0)
                    if piece.color == self.color:
                        total += value + self.evaluate_piece_position(piece, row_index, col_index)
                        # Additional heuristics for AI's own pieces
                        if board.is_in_check(self.color):
                            total -= 200  # Penalize being in check
                    else:
                        total -= value + self.evaluate_piece_position(piece, row_index, col_index)
                        # Additional heuristics for opponent's pieces
                        if board.is_in_check(self.opponent_color):
                            total += 200  # Reward if opponent is in check
        return total

    def evaluate_piece_position(self, piece, row, col):
        if piece.name in self.piece_square_tables:
            table = self.piece_square_tables[piece.name]
            if piece.color == 'white':
                return table[row][col]
            else:
                return table[7 - row][col]
        return 0

    def evaluate_piece_value(self, piece):
        piece_value = {
            'pawn': 100,
            'knight': 320,
            'bishop': 330,
            'rook': 500,
            'queen': 900,
            'king': 20000
        }
        return piece_value.get(piece.name, 0)
