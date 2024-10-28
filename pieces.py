# pieces.py

class Piece:
    def __init__(self, color):
        self.color = color
        self.name = ''
        self.has_moved = False

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        raise NotImplementedError("This method should be implemented by subclasses.")

class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.name = 'pawn'
        self.direction = -1 if color == 'white' else 1

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        move_forward = end_row - start_row
        diff_col = end_col - start_col
        direction = self.direction

        if diff_col == 0:
            if move_forward == direction and not board.get_piece(end_row, end_col):
                return True
            if move_forward == 2 * direction and not self.has_moved:
                intermediate_row = start_row + direction
                if not board.get_piece(intermediate_row, start_col) and not board.get_piece(end_row, end_col):
                    return True
        elif abs(diff_col) == 1 and move_forward == direction:
            target_piece = board.get_piece(end_row, end_col)
            if target_piece and target_piece.color != self.color:
                return True
            # En Passant (Placeholder)
            # TODO: Implement en passant logic if desired
        return False

class Rook(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.name = 'rook'

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        if start_row != end_row and start_col != end_col:
            return False
        if start_row == end_row:
            step = 1 if end_col > start_col else -1
            for col in range(start_col + step, end_col, step):
                if board.get_piece(start_row, col):
                    return False
            return True
        else:
            step = 1 if end_row > start_row else -1
            for row in range(start_row + step, end_row, step):
                if board.get_piece(row, start_col):
                    return False
            return True

class Knight(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.name = 'knight'

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        row_diff = abs(end_row - start_row)
        col_diff = abs(end_col - start_col)
        if (row_diff, col_diff) in [(2, 1), (1, 2)]:
            target_piece = board.get_piece(end_row, end_col)
            if not target_piece or target_piece.color != self.color:
                return True
        return False

class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.name = 'bishop'

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        if abs(start_row - end_row) != abs(start_col - end_col):
            return False
        step_row = 1 if end_row > start_row else -1
        step_col = 1 if end_col > start_col else -1
        for i in range(1, abs(end_row - start_row)):
            if board.get_piece(start_row + i * step_row, start_col + i * step_col):
                return False
        target_piece = board.get_piece(end_row, end_col)
        if not target_piece or target_piece.color != self.color:
            return True
        return False

class Queen(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.name = 'queen'

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        rook_move = Rook(self.color).is_valid_move(start_row, start_col, end_row, end_col, board)
        bishop_move = Bishop(self.color).is_valid_move(start_row, start_col, end_row, end_col, board)
        return rook_move or bishop_move

class King(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.name = 'king'

    def is_valid_move(self, start_row, start_col, end_row, end_col, board):
        if max(abs(end_row - start_row), abs(end_col - start_col)) == 1:
            target_piece = board.get_piece(end_row, end_col)
            if not target_piece or target_piece.color != self.color:
                return True
        if not self.has_moved and start_row == end_row and abs(end_col - start_col) == 2:
            return self.can_castle(start_row, start_col, end_row, end_col, board)
        return False

    def can_castle(self, start_row, start_col, end_row, end_col, board):
        if end_col == 6:
            rook = board.get_piece(start_row, 7)
            if isinstance(rook, Rook) and not rook.has_moved:
                if not board.get_piece(start_row, 5) and not board.get_piece(start_row, 6):
                    if not board.is_in_check(self.color) and not board.would_be_in_check(self.color, start_row, start_col, start_row, 5):
                        return True
        elif end_col == 2:
            rook = board.get_piece(start_row, 0)
            if isinstance(rook, Rook) and not rook.has_moved:
                if not board.get_piece(start_row, 1) and not board.get_piece(start_row, 2) and not board.get_piece(start_row, 3):
                    if not board.is_in_check(self.color) and not board.would_be_in_check(self.color, start_row, start_col, start_row, 3):
                        return True
        return False
