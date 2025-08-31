import random
import time
from pieces import King, Rook, Queen, Bishop, Knight, Pawn

class AI:
    def __init__(self, color):
        self.color = color
        self.opponent_color = 'black' if color == 'white' else 'white'
        self.depth = 4
        # Tapered evaluation piece-square tables (MG/EG)
        self.pst_mg, self.pst_eg = self.initialize_piece_square_tables()
        self.transposition_table = {}
        self.zobrist_keys = self.initialize_zobrist_keys()
        self.MATE_VALUE = 1000000
        # Move ordering helpers
        self.history = {}
        self.killers = {}
        # Time management (milliseconds per move). None = unlimited
        self.time_ms = 1500
        self._deadline = None
        self._aborted = False

    def initialize_piece_square_tables(self):
        # Midgame piece-square tables (values in centipawns)
        pawn = [
            [0,   0,   0,   0,   0,   0,   0,   0],
            [50,  50,  50,  50,  50,  50,  50,  50],
            [10,  10,  20,  30,  30,  20,  10,  10],
            [5,   5,  10,  25,  25,  10,   5,   5],
            [0,   0,   0,  20,  20,   0,   0,   0],
            [5,  -5, -10,   0,   0, -10, -5,   5],
            [5,  10,  10, -20, -20,  10, 10,   5],
            [0,   0,   0,   0,   0,   0,  0,   0],
        ]
        knight = [
            [-50, -40, -30, -30, -30, -30, -40, -50],
            [-40, -20,   0,   0,   0,   0, -20, -40],
            [-30,   0,  10,  15,  15,  10,   0, -30],
            [-30,   5,  15,  20,  20,  15,   5, -30],
            [-30,   0,  15,  20,  20,  15,   0, -30],
            [-30,   5,  10,  15,  15,  10,   5, -30],
            [-40, -20,   0,   5,   5,   0, -20, -40],
            [-50, -40, -30, -30, -30, -30, -40, -50],
        ]
        bishop = [
            [-20, -10, -10, -10, -10, -10, -10, -20],
            [-10,   5,   0,   0,   0,   0,   5, -10],
            [-10,  10,  10,  10,  10,  10,  10, -10],
            [-10,   0,  10,  10,  10,  10,   0, -10],
            [-10,   5,   5,  10,  10,   5,   5, -10],
            [-10,   0,   5,  10,  10,   5,   0, -10],
            [-10,   0,   0,   0,   0,   0,   0, -10],
            [-20, -10, -10, -10, -10, -10, -10, -20],
        ]
        rook = [
            [0,   0,  5,  10,  10,   5,   0,   0],
            [-5,  0,  0,   0,   0,   0,   0,  -5],
            [-5,  0,  0,   0,   0,   0,   0,  -5],
            [-5,  0,  0,   0,   0,   0,   0,  -5],
            [-5,  0,  0,   0,   0,   0,   0,  -5],
            [-5,  0,  0,   0,   0,   0,   0,  -5],
            [5,  10, 10,  10,  10,  10,  10,  5],
            [0,   0,  0,   0,   0,   0,   0,   0],
        ]
        queen = [
            [-20, -10, -10, -5, -5, -10, -10, -20],
            [-10,   0,   5,  0,  0,   0,   0, -10],
            [-10,   5,   5,  5,  5,   5,   0, -10],
            [ -5,   0,   5,  5,  5,   5,   0,  -5],
            [  0,   0,   5,  5,  5,   5,   0,  -5],
            [-10,   5,   5,  5,  5,   5,   0, -10],
            [-10,   0,   5,  0,  0,   0,   0, -10],
            [-20, -10, -10, -5, -5, -10, -10, -20],
        ]
        king_mg = [
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-20, -30, -30, -40, -40, -30, -30, -20],
            [-10, -20, -20, -20, -20, -20, -20, -10],
            [ 20,  20,   0,   0,   0,   0,  20,  20],
            [ 20,  30,  10,   0,   0,  10,  30,  20],
        ]
        # Endgame king table (centralization)
        king_eg = [
            [-50, -40, -30, -20, -20, -30, -40, -50],
            [-40, -20,   0,  10,  10,   0, -20, -40],
            [-30,  10,  20,  30,  30,  20,  10, -30],
            [-20,  20,  40,  50,  50,  40,  20, -20],
            [-20,  20,  40,  50,  50,  40,  20, -20],
            [-30,  10,  20,  30,  30,  20,  10, -30],
            [-40, -20,   0,  10,  10,   0, -20, -40],
            [-50, -40, -30, -20, -20, -30, -40, -50],
        ]

        pst_mg = {'pawn': pawn, 'knight': knight, 'bishop': bishop, 'rook': rook, 'queen': queen, 'king': king_mg}
        pst_eg = {'pawn': pawn, 'knight': knight, 'bishop': bishop, 'rook': rook, 'queen': queen, 'king': king_eg}
        return pst_mg, pst_eg

    def initialize_zobrist_keys(self):
        random.seed(0)
        zobrist = {}
        pieces = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
        colors = ['white', 'black']
        for piece in pieces:
            for color in colors:
                for square in range(64):
                    zobrist[(piece, color, square)] = random.getrandbits(64)
        zobrist['white_to_move'] = random.getrandbits(64)
        # Castling rights
        for k in ['WK', 'WQ', 'BK', 'BQ']:
            zobrist[f'castling_{k}'] = random.getrandbits(64)
        return zobrist

    def get_move(self, board):
        # Iterative deepening at root; preserves best move each iteration
        moves = self.get_all_moves(board, self.color)
        if not moves:
            return None

        best_move = moves[0]
        # Root hash with side to move
        root_hash = self.hash_board(board)
        if self.color == 'white':
            root_hash ^= self.zobrist_keys['white_to_move']
        tt_move = None
        entry = self.transposition_table.get(root_hash)
        if entry:
            _, _, _, tt_move = entry

        # Initialize time budget
        self._aborted = False
        self._deadline = (time.time() + self.time_ms / 1000.0) if self.time_ms else None

        prev_score = 0
        for depth in range(1, self.depth + 1):
            alpha = float('-inf')
            beta = float('inf')
            best_score = float('-inf')
            # Simple aspiration window around previous iteration score
            if depth > 1:
                window = 50
                alpha = prev_score - window
                beta = prev_score + window
            for move in self.order_moves(moves, board, tt_move=tt_move, depth=depth):
                if self._deadline and time.time() >= self._deadline:
                    self._aborted = True
                    break
                board.make_move(*move[0], *move[1], switch_turn=False, validate=False)
                try:
                    score = self.alpha_beta(board, depth - 1, alpha, beta, False)
                except TimeoutError:
                    self._aborted = True
                    score = float('-inf')
                finally:
                    board.unmake_move(switch_turn=False)
                if score > best_score:
                    best_score = score
                    best_move = move
                if score > alpha:
                    alpha = score
                if beta <= alpha or self._aborted:
                    break
            tt_move = best_move
            prev_score = best_score
            if self._aborted:
                break

        return best_move

    def alpha_beta(self, board, depth, alpha, beta, is_maximizing):
        color_to_move = self.color if is_maximizing else self.opponent_color
        board_hash = self.hash_board(board)
        if color_to_move == 'white':
            board_hash ^= self.zobrist_keys['white_to_move']

        # Time check
        if self._deadline and time.time() >= self._deadline:
            raise TimeoutError()

        entry = self.transposition_table.get(board_hash)
        if entry and entry[0] >= depth:
            _, tt_flag, tt_value, _ = entry
            if tt_flag == 'EXACT':
                return tt_value
            elif tt_flag == 'LOWERBOUND':
                alpha = max(alpha, tt_value)
            elif tt_flag == 'UPPERBOUND':
                beta = min(beta, tt_value)
            if alpha >= beta:
                return tt_value

        if depth == 0:
            return self.qsearch(board, alpha, beta, is_maximizing)

        # Null-move pruning (skip if in check)
        if depth >= 3 and not board.is_in_check(color_to_move):
            R = 2 + (depth // 6)
            if is_maximizing:
                val = self.alpha_beta(board, depth - 1 - R, alpha, beta, False)
                if val >= beta:
                    return val
            else:
                val = self.alpha_beta(board, depth - 1 - R, alpha, beta, True)
                if val <= alpha:
                    return val

        moves = self.get_all_moves(board, color_to_move)
        if not moves:
            if board.is_in_check(color_to_move):
                # Checkmate: current side to move is mated
                return -self.MATE_VALUE if is_maximizing else self.MATE_VALUE
            # Stalemate
            return 0

        tt_move = entry[3] if entry else None
        a0, b0 = alpha, beta
        best_move = None

        if is_maximizing:
            best_value = float('-inf')
            first = True
            ordered = self.order_moves(moves, board, tt_move=tt_move, depth=depth)
            for idx, move in enumerate(ordered):
                (sr, sc), (er, ec) = move
                target = board.get_piece(er, ec)
                board.make_move(sr, sc, er, ec, switch_turn=False, validate=False)
                try:
                    if first:
                        value = self.alpha_beta(board, depth - 1, alpha, beta, False)
                        first = False
                    else:
                        # Late Move Reductions for late quiet moves
                        reduced = 0
                        if depth >= 3 and idx > 3 and not target:
                            reduced = 1
                        # Principal Variation Search (zero-window)
                        value = self.alpha_beta(board, depth - 1 - reduced, alpha, alpha + 1, False)
                        if value > alpha and value < beta and reduced:
                            value = self.alpha_beta(board, depth - 1, alpha, alpha + 1, False)
                        if value > alpha and value < beta:
                            value = self.alpha_beta(board, depth - 1, alpha, beta, False)
                finally:
                    board.unmake_move(switch_turn=False)
                if value > best_value:
                    best_value = value
                    best_move = move
                if value > alpha:
                    alpha = value
                    # History heuristic: reward quiet PV moves
                    if not target:
                        self.history[(sr, sc, er, ec)] = self.history.get((sr, sc, er, ec), 0) + depth * depth
                if alpha >= beta:
                    # Killer heuristic: record quiet beta-cutoff moves
                    if not target:
                        km = self.killers.get(depth, [])
                        if not km:
                            self.killers[depth] = [move]
                        elif move != km[0]:
                            self.killers[depth] = [move, km[0]]
                    break
            flag = 'EXACT'
            if best_value <= a0:
                flag = 'UPPERBOUND'
            elif best_value >= b0:
                flag = 'LOWERBOUND'
            self.transposition_table[board_hash] = (depth, flag, best_value, best_move)
            return best_value
        else:
            best_value = float('inf')
            first = True
            ordered = self.order_moves(moves, board, tt_move=tt_move, depth=depth)
            for idx, move in enumerate(ordered):
                (sr, sc), (er, ec) = move
                target = board.get_piece(er, ec)
                board.make_move(sr, sc, er, ec, switch_turn=False, validate=False)
                try:
                    if first:
                        value = self.alpha_beta(board, depth - 1, alpha, beta, True)
                        first = False
                    else:
                        reduced = 0
                        if depth >= 3 and idx > 3 and not target:
                            reduced = 1
                        value = self.alpha_beta(board, depth - 1 - reduced, beta - 1, beta, True)
                        if value < beta and value > alpha and reduced:
                            value = self.alpha_beta(board, depth - 1, beta - 1, beta, True)
                        if value < beta and value > alpha:
                            value = self.alpha_beta(board, depth - 1, alpha, beta, True)
                finally:
                    board.unmake_move(switch_turn=False)
                if value < best_value:
                    best_value = value
                    best_move = move
                if value < beta:
                    beta = value
                    if not target:
                        self.history[(sr, sc, er, ec)] = self.history.get((sr, sc, er, ec), 0) + depth * depth
                if alpha >= beta:
                    if not target:
                        km = self.killers.get(depth, [])
                        if not km:
                            self.killers[depth] = [move]
                        elif move != km[0]:
                            self.killers[depth] = [move, km[0]]
                    break
            flag = 'EXACT'
            if best_value >= b0:
                flag = 'LOWERBOUND'
            elif best_value <= a0:
                flag = 'UPPERBOUND'
            self.transposition_table[board_hash] = (depth, flag, best_value, best_move)
            return best_value

    def hash_board(self, board):
        h = 0
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece:
                    square = row * 8 + col
                    h ^= self.zobrist_keys.get((piece.name, piece.color, square), 0)
        # Approximate castling rights from piece.has_moved flags at start squares
        # White
        wk = board.get_piece(7, 4)
        wr_a = board.get_piece(7, 0)
        wr_h = board.get_piece(7, 7)
        if isinstance(wk, King) and not wk.has_moved:
            if isinstance(wr_h, Rook) and not wr_h.has_moved:
                h ^= self.zobrist_keys['castling_WK']
            if isinstance(wr_a, Rook) and not wr_a.has_moved:
                h ^= self.zobrist_keys['castling_WQ']
        # Black
        bk = board.get_piece(0, 4)
        br_a = board.get_piece(0, 0)
        br_h = board.get_piece(0, 7)
        if isinstance(bk, King) and not bk.has_moved:
            if isinstance(br_h, Rook) and not br_h.has_moved:
                h ^= self.zobrist_keys['castling_BK']
            if isinstance(br_a, Rook) and not br_a.has_moved:
                h ^= self.zobrist_keys['castling_BQ']
        return h

    def get_all_moves(self, board, color):
        moves = []
        for start, end in board.generate_pseudolegal_moves(color):
            (sr, sc), (er, ec) = start, end
            if not board.would_be_in_check(color, sr, sc, er, ec):
                moves.append((start, end))
        return moves

    def order_moves(self, moves, board, tt_move=None, depth=None):
        piece_value = {
            'pawn': 100,
            'knight': 320,
            'bishop': 330,
            'rook': 500,
            'queen': 900,
            'king': 20000
        }

        def mvv_lva_score(move):
            (sr, sc), (er, ec) = move
            attacker = board.get_piece(sr, sc)
            target = board.get_piece(er, ec)
            capture_bonus = 0
            if target:
                capture_bonus = 10000 + piece_value.get(target.name, 0) - 0.1 * piece_value.get(attacker.name, 0)
            # Small preference by attacker mobility order (encourage forcing moves first)
            attacker_bias = {
                'queen': 6,
                'rook': 5,
                'bishop': 3,
                'knight': 3,
                'pawn': 1,
                'king': 0,
            }.get(attacker.name, 0)
            tt_bonus = 500000 if tt_move and move == tt_move else 0
            # Killer/history for quiet moves
            killer_bonus = 0
            hist_bonus = 0
            if not target and depth is not None:
                killers = self.killers.get(depth, [])
                if killers:
                    if move == killers[0]:
                        killer_bonus = 30000
                    elif len(killers) > 1 and move == killers[1]:
                        killer_bonus = 20000
                hist_bonus = self.history.get((sr, sc, er, ec), 0)
            return tt_bonus + capture_bonus + killer_bonus + hist_bonus + attacker_bias

        return sorted(moves, key=mvv_lva_score, reverse=True)

    def get_all_captures(self, board, color):
        captures = []
        for start, end in board.generate_pseudolegal_moves(color):
            (sr, sc), (er, ec) = start, end
            target = board.get_piece(er, ec)
            if target and target.color != color:
                if not board.would_be_in_check(color, sr, sc, er, ec):
                    captures.append((start, end))
        return captures

    def qsearch(self, board, alpha, beta, is_maximizing):
        # Time check
        if self._deadline and time.time() >= self._deadline:
            raise TimeoutError()
        # Static evaluation as stand-pat
        stand_pat = self.evaluate_board(board)
        if is_maximizing:
            if stand_pat >= beta:
                return stand_pat
            if alpha < stand_pat:
                alpha = stand_pat
            moves = self.get_all_captures(board, self.color)
            for move in self.order_moves(moves, board, depth=0):
                board.make_move(*move[0], *move[1], switch_turn=False, validate=False)
                score = self.qsearch(board, alpha, beta, False)
                board.unmake_move(switch_turn=False)
                if score >= beta:
                    return score
                if score > alpha:
                    alpha = score
            return alpha
        else:
            if stand_pat <= alpha:
                return stand_pat
            if beta > stand_pat:
                beta = stand_pat
            moves = self.get_all_captures(board, self.opponent_color)
            for move in self.order_moves(moves, board, depth=0):
                board.make_move(*move[0], *move[1], switch_turn=False, validate=False)
                score = self.qsearch(board, alpha, beta, True)
                board.unmake_move(switch_turn=False)
                if score <= alpha:
                    return score
                if score < beta:
                    beta = score
            return beta

    def evaluate_board(self, board):
        # Material values (centipawns)
        PV = {'pawn': 100, 'knight': 320, 'bishop': 330, 'rook': 500, 'queen': 900, 'king': 0}

        mg_white = 0
        mg_black = 0
        eg_white = 0
        eg_black = 0

        pawns_file_white = [0] * 8
        pawns_file_black = [0] * 8
        bishop_count = {'white': 0, 'black': 0}
        rook_squares = {'white': [], 'black': []}
        king_pos = {'white': None, 'black': None}

        # Scan board once
        for r in range(8):
            row = board.board[r]
            for c in range(8):
                piece = row[c]
                if not piece:
                    continue
                name = piece.name
                color = piece.color
                val = PV.get(name, 0)

                # PST: white uses table as-is, black mirrored vertically
                if color == 'white':
                    mg = val + self.pst_mg[name][r][c]
                    eg = val + self.pst_eg[name][r][c]
                else:
                    mg = val + self.pst_mg[name][7 - r][c]
                    eg = val + self.pst_eg[name][7 - r][c]

                if color == 'white':
                    mg_white += mg
                    eg_white += eg
                else:
                    mg_black += mg
                    eg_black += eg

                if name == 'pawn':
                    if color == 'white':
                        pawns_file_white[c] += 1
                    else:
                        pawns_file_black[c] += 1
                elif name == 'bishop':
                    bishop_count[color] += 1
                elif name == 'rook':
                    rook_squares[color].append((r, c))
                elif name == 'king':
                    king_pos[color] = (r, c)

        # Bishop pair bonus
        if bishop_count['white'] >= 2:
            mg_white += 30
            eg_white += 40
        if bishop_count['black'] >= 2:
            mg_black += 30
            eg_black += 40

        # Pawn structure: doubled and isolated
        for file in range(8):
            w_count = pawns_file_white[file]
            b_count = pawns_file_black[file]
            if w_count > 1:
                mg_white -= 20 * (w_count - 1)
                eg_white -= 10 * (w_count - 1)
            if b_count > 1:
                mg_black -= 20 * (b_count - 1)
                eg_black -= 10 * (b_count - 1)
            # Isolated: no friendly pawns on adjacent files
            w_adj = (pawns_file_white[file - 1] if file - 1 >= 0 else 0) + (pawns_file_white[file + 1] if file + 1 <= 7 else 0)
            b_adj = (pawns_file_black[file - 1] if file - 1 >= 0 else 0) + (pawns_file_black[file + 1] if file + 1 <= 7 else 0)
            if w_count > 0 and w_adj == 0:
                mg_white -= 15
                eg_white -= 10
            if b_count > 0 and b_adj == 0:
                mg_black -= 15
                eg_black -= 10

        # Passed pawns (simple): no enemy pawns on same/adjacent files ahead
        def passed_bonus(color, r, c):
            rank_from_white = r
            if color == 'white':
                ahead_rows = range(0, r)
                files = [max(0, c - 1), c, min(7, c + 1)]
                if sum(pawns_file_black[f] for f in set(files)) == 0:
                    # closer to promotion -> higher bonus
                    return (6 - r) * 10
            else:
                ahead_rows = range(r + 1, 8)
                files = [max(0, c - 1), c, min(7, c + 1)]
                if sum(pawns_file_white[f] for f in set(files)) == 0:
                    return (r - 1) * 10
            return 0

        for r in range(8):
            for c in range(8):
                p = board.get_piece(r, c)
                if p and p.name == 'pawn':
                    bonus = passed_bonus(p.color, r, c)
                    if p.color == 'white':
                        mg_white += bonus
                        eg_white += bonus + 10
                    else:
                        mg_black += bonus
                        eg_black += bonus + 10

        # Rooks on open/semi-open files
        for (r, c) in rook_squares['white']:
            if pawns_file_white[c] == 0 and pawns_file_black[c] == 0:
                mg_white += 20; eg_white += 15
            elif pawns_file_white[c] == 0:
                mg_white += 10; eg_white += 8
        for (r, c) in rook_squares['black']:
            if pawns_file_black[c] == 0 and pawns_file_white[c] == 0:
                mg_black += 20; eg_black += 15
            elif pawns_file_black[c] == 0:
                mg_black += 10; eg_black += 8

        # King safety: pawn shield (home files)
        def pawn_shield(color, king_pos):
            if not king_pos:
                return 0
            r, c = king_pos
            bonus = 0
            cols = [max(0, c - 1), c, min(7, c + 1)]
            if color == 'white':
                # rows 6 and 5 (second and third ranks from white perspective)
                for rr in [6, 5]:
                    for cc in cols:
                        p = board.get_piece(rr, cc)
                        if p and p.name == 'pawn' and p.color == 'white':
                            bonus += 6 if rr == 6 else 3
            else:
                for rr in [1, 2]:
                    for cc in cols:
                        p = board.get_piece(rr, cc)
                        if p and p.name == 'pawn' and p.color == 'black':
                            bonus += 6 if rr == 1 else 3
            return bonus

        mg_white += pawn_shield('white', king_pos['white'])
        mg_black += pawn_shield('black', king_pos['black'])

        # Center control bonus for occupying central squares
        centers = {(3, 3), (3, 4), (4, 3), (4, 4)}
        for (r, c) in centers:
            p = board.get_piece(r, c)
            if p:
                if p.color == 'white':
                    mg_white += 5
                else:
                    mg_black += 5

        # Very light mobility (costly, so apply small weight)
        def mobility(color):
            total = 0
            for row, col, pc in board.get_all_pieces(color):
                if pc.name in ('bishop', 'rook', 'queen', 'knight'):
                    total += len(board.generate_pseudolegal_moves_from_square(row, col))
            return total

        mob_w = mobility('white')
        mob_b = mobility('black')
        mg_white += mob_w // 2
        mg_black += mob_b // 2

        # Game phase based on remaining non-pawn material (roughly 24 at opening)
        phase_weights = {'pawn': 0, 'knight': 1, 'bishop': 1, 'rook': 2, 'queen': 4, 'king': 0}
        max_phase = 24
        phase = 0
        for r in range(8):
            for c in range(8):
                p = board.get_piece(r, c)
                if p:
                    phase += phase_weights.get(p.name, 0)
        phase = max(0, min(max_phase, phase))

        mg_score = mg_white - mg_black
        eg_score = eg_white - eg_black
        score = (mg_score * phase + eg_score * (max_phase - phase)) // max_phase

        # Mild check adjustment
        if board.is_in_check('white'):
            score -= 15
        if board.is_in_check('black'):
            score += 15

        # Return from perspective of self.color
        return score if self.color == 'white' else -score

    def evaluate_piece_position(self, piece, row, col):
        # Deprecated by the new tapered eval, kept for compatibility
        table = self.pst_mg.get(piece.name)
        if not table:
            return 0
        if piece.color == 'white':
            return table[row][col]
        return table[7 - row][col]

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
