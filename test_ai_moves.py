#!/usr/bin/env python3
"""
Test script to validate AI move logic without pygame dependencies
"""

class MockBoard:
    def __init__(self):
        self.current_turn = 'white'
        self.move_history = []
    
    def make_move(self, sr, sc, er, ec):
        # Mock successful move
        move = {
            'piece': MockPiece(self.current_turn),
            'start_pos': (sr, sc),
            'end_pos': (er, ec)
        }
        self.move_history.append(move)
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        return True

class MockPiece:
    def __init__(self, color):
        self.color = color
        self.name = 'pawn'

class MockAI:
    def __init__(self):
        self.move_count = 0
    
    def get_move(self, board):
        self.move_count += 1
        return ((1, 0), (3, 0))  # Mock move

# Test the game logic without pygame
class TestGame:
    def __init__(self):
        self.board = MockBoard()
        self.ai = MockAI()
        self.game_over = False
        self.in_review = False
        self.last_move_color = None
        self.waiting_for_white = False
        self.last_ai_move_count = -1
        
    def _refresh_last_move_color(self):
        if not self.board.move_history:
            self.last_move_color = None
            if self.board.current_turn == 'white':
                self.waiting_for_white = False
        else:
            last_move_piece = self.board.move_history[-1]['piece']
            self.last_move_color = last_move_piece.color
    
    def update(self):
        self._refresh_last_move_color()
        
        if not self.game_over and self.board.current_turn == 'black' and not self.in_review:
            print(f"AI turn check: move_history={len(self.board.move_history)}, last_move_color={self.last_move_color}, waiting_for_white={self.waiting_for_white}")
            
            current_move_count = len(self.board.move_history)
            
            if self.last_ai_move_count == current_move_count:
                print("Skipping AI move - AI already moved this turn")
                return False
            
            if self.last_move_color == 'black':
                print("Skipping AI move - last move was also by black")
                return False
                
            if self.waiting_for_white:
                print("Skipping AI move - waiting for white to move")
                return False
            
            if self.board.current_turn != 'black':
                print("Skipping AI move - not black's turn")
                return False
                
            move = self.ai.get_move(self.board)
            if move:
                start_pos, end_pos = move
                print(f"AI making move from {start_pos} to {end_pos}")
                if self.board.make_move(*start_pos, *end_pos):
                    print(f"AI moved successfully")
                    self.last_move_color = 'black'
                    self.waiting_for_white = True
                    self.last_ai_move_count = len(self.board.move_history)
                    return True
        return False
    
    def make_white_move(self):
        if self.board.current_turn == 'white':
            print("White making move")
            if self.board.make_move(6, 0, 4, 0):  # Mock white move
                self.last_move_color = 'white'
                self.waiting_for_white = False
                self.last_ai_move_count = -1
                return True
        return False

def test_alternating_moves():
    print("=== Testing AI Move Prevention ===")
    game = TestGame()
    
    # Test 1: Initial state - white should move first
    print("\n1. Initial state:")
    result = game.update()
    print(f"AI moved: {result} (should be False - white goes first)")
    
    # Test 2: After white moves, AI should be able to move
    print("\n2. After white move:")
    game.make_white_move()
    result = game.update()
    print(f"AI moved: {result} (should be True)")
    
    # Test 3: Multiple AI update calls should not result in multiple moves
    print("\n3. Multiple AI update calls:")
    result1 = game.update()
    result2 = game.update()
    result3 = game.update()
    print(f"AI moves: {result1}, {result2}, {result3} (should be False, False, False)")
    
    # Test 4: After white moves again, AI should be able to move once more
    print("\n4. After another white move:")
    game.make_white_move()
    result = game.update()
    print(f"AI moved: {result} (should be True)")
    
    print(f"\nFinal AI move count: {game.ai.move_count} (should be 2)")
    print(f"Total game moves: {len(game.board.move_history)} (should be 4)")

if __name__ == "__main__":
    test_alternating_moves()
