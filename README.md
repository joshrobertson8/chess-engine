# Chess Game with AI - README

## Overview
This project is a **Python-based chess game** with a graphical interface and an AI opponent implemented using **Pygame**. Players control the white pieces, while the AI controls the black pieces with a difficulty setting of **hard** by default, using a depth-based minimax algorithm with alpha-beta pruning. The game supports essential chess mechanics, including auto-promotion to a queen and kingside-only castling.

## Features
1. **Graphical Interface:** Displayed through Pygame, with interactive piece movement, check indications, and an endgame message for checkmate, stalemate, or draw.
2. **AI Opponent:** The AI operates on a depth-based strategy using:
   - Piece-square tables for strategic positioning.
   - A transposition table to optimize move evaluations.
   - Minimax with alpha-beta pruning to determine optimal moves.
   - Operates on a depth of 4 moves
   - Estimated Elo ranges from 500-600
3. **Chess Mechanics:** 
   - **Kingside Castling** and **Auto Queen Promotion** are implemented.
   - **Check** and **Checkmate** detection.
   - **Stalemate** detection.

## Project Structure
- **`ai.py`**: Contains the AI class that calculates optimal moves using piece-square tables, transposition tables, and minimax algorithm.
- **`board.py`**: Manages the board state, including move validation, piece placement, and capturing mechanics.
- **`game.py`**: Handles the main game logic, player interactions, and screen updates.
- **`main.py`**: Initializes the game, creating a game window and starting the game loop.
- **`pieces.py`**: Defines each chess piece (Pawn, Rook, Knight, Bishop, Queen, King) and their unique movement rules.

## Getting Started
### Prerequisites
- Python 3.x
- Pygame library: Install using `pip install pygame`

### Cloning the Repository
To get started, clone the repository using the following command:
```bash
git clone https://github.com/joshrobertson8/chess-engine.git
cd chess-engine
cd python main.py
