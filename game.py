# game.py
import pygame
from board import Board
from ai import AI

DEBUG = False

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.board = Board()
        self.selected_piece = None
        # Typography
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 22)
        self.tiny_font = pygame.font.SysFont(None, 16)
        self.ai = AI('black')  # AI always plays as black with hard difficulty
        self.game_over = False
        self.winner = None
        # Sidebar and review/analysis state
        self.sidebar_width = 300
        self.board_pixels = 800
        self.redo_stack = []  # for forward stepping
        self.in_review = False
        self.analysis_enabled = False
        self.analysis_depth = 2
        self.analysis_result = None  # (best_move, score)
        self.last_analyzed_ply = -1
        self.move_scroll = 0  # for scrolling move list
        self.live_chip_rect = None
        # Built-in engine analysis only
        self.last_move_color = None

        # UI palette
        self.UI_BG = (30, 34, 40)
        self.UI_PANEL = (39, 45, 55)
        self.UI_PANEL_BORDER = (24, 28, 34)
        self.UI_TEXT = (230, 232, 235)
        self.UI_TEXT_MUTED = (165, 170, 180)
        self.UI_ACCENT = (79, 138, 247)   # blue
        self.UI_ACCENT_ON = (46, 204, 113)  # green
        self.UI_BUTTON = (60, 68, 80)
        self.UI_BUTTON_HOVER = (70, 78, 92)
        self.UI_STRIPE = (44, 50, 60)

        # Precompute sidebar button rects
        x0 = self.board_pixels + 10
        y0 = 10
        w = 46
        h = 40
        gap = 8
        self.btn_to_start = pygame.Rect(x0, y0, w, h)
        self.btn_back = pygame.Rect(x0 + (w + gap), y0, w, h)
        self.btn_forward = pygame.Rect(x0 + 2 * (w + gap), y0, w, h)
        self.btn_to_end = pygame.Rect(x0 + 3 * (w + gap), y0, w, h)
        y1 = y0 + h + 12
        # Width/pos of analyze pill is set dynamically to avoid overlap with the Live chip
        self.btn_analyze = pygame.Rect(x0, y1, 200, h)

    def update_sidebar_layout_geometry(self):
        # Recompute dynamic sidebar layout each frame for consistent hitboxes
        x = self.board_pixels
        ctrl_rect = pygame.Rect(x + 6, 6, self.sidebar_width - 12, 96)
        y0 = 10
        h = 40
        y1 = y0 + h + 12
        # Leave space on the right for the Live chip
        available_w = ctrl_rect.w - 100 - 24
        self.btn_analyze.x = ctrl_rect.x + 10
        self.btn_analyze.y = y1
        self.btn_analyze.w = max(120, available_w)
        self.btn_analyze.h = h
        # Live chip rect (doesn't handle clicks; purely visual for now)
        chip_w, chip_h = 80, 26
        self.live_chip_rect = pygame.Rect(ctrl_rect.right - (chip_w + 10), y1 + (h - chip_h) // 2, chip_w, chip_h)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                # Sidebar click handling always active
                if pos[0] >= self.board_pixels:
                    # Keep geometry up to date before hit-testing
                    self.update_sidebar_layout_geometry()
                    self.handle_sidebar_click(pos)
                    continue
            if event.type == pygame.MOUSEWHEEL:
                # Scroll move list
                self.move_scroll -= event.y * 2  # smooth-ish scrolling
                self.move_scroll = max(0, min(self.move_scroll, max(0, len(self.board.move_history) - 1)))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.step_back()
                elif event.key == pygame.K_RIGHT:
                    self.step_forward()
                elif event.key == pygame.K_HOME:
                    self.go_to_start()
                elif event.key == pygame.K_END:
                    self.go_to_end()
                elif event.key == pygame.K_a:
                    self.analysis_enabled = not self.analysis_enabled
                    self.analysis_result = None
                    self.last_analyzed_ply = -1

            if not self.game_over and self.board.current_turn == 'white' and not self.in_review:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    row, col = pos[1] // 100, pos[0] // 100
                    if DEBUG:
                        print(f"User clicked on ({row}, {col})")
                    if self.selected_piece is None:
                        piece = self.board.get_piece(row, col)
                        if piece and piece.color == 'white':
                            self.selected_piece = (row, col, piece)
                            if DEBUG:
                                print(f"Selected {piece.color} {piece.name} at ({row}, {col})")
                    else:
                        start_row, start_col, piece = self.selected_piece
                        if DEBUG:
                            print(f"Attempting to move {piece.color} {piece.name} from ({start_row}, {start_col}) to ({row}, {col})")
                        if (start_row, start_col) != (row, col):
                            move_successful = self.board.make_move(start_row, start_col, row, col)
                            if move_successful:
                                if DEBUG:
                                    print(f"Move successful: {piece.color} {piece.name} moved to ({row}, {col})")
                                self.last_move_color = 'white'
                                self.check_game_over()
                            else:
                                if DEBUG:
                                    print("Move failed. Invalid move.")
                                # Optional: Provide feedback to the player
                        else:
                            if DEBUG:
                                print("Clicked on the same square. Deselecting piece.")
                        self.selected_piece = None

    def update(self):
        if not self.game_over and self.board.current_turn == 'black' and not self.in_review:
            if DEBUG:
                print("AI's turn.")
            # Guard against accidental consecutive AI moves
            if self.last_move_color == 'black':
                return
            move = self.ai.get_move(self.board)
            if move:
                start_pos, end_pos = move
                if DEBUG:
                    print(f"AI attempting to move from {start_pos} to {end_pos}")
                if self.board.make_move(*start_pos, *end_pos):
                    if DEBUG:
                        print(f"AI moved from {start_pos} to {end_pos}")
                    self.last_move_color = 'black'
                    self.check_game_over()
                else:
                    if DEBUG:
                        print("AI attempted an invalid move.")
            else:
                if DEBUG:
                    print("AI has no valid moves. Game over.")
                self.game_over = True
                self.winner = 'White'

    def draw(self):
        # Fill sidebar background first
        pygame.draw.rect(self.screen, self.UI_BG, (self.board_pixels, 0, self.sidebar_width, 800))

        # Draw chessboard area
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
        # Sidebar UI
        self.update_sidebar_layout_geometry()
        self.draw_sidebar()
        pygame.display.flip()

    def check_game_over(self):
        if DEBUG:
            print("Checking if the game is over...")
        if self.board.is_checkmate('black'):
            self.game_over = True
            self.winner = 'White'
            if DEBUG:
                print("Checkmate detected. White wins!")
        elif self.board.is_checkmate('white'):
            self.game_over = True
            self.winner = 'Black'
            if DEBUG:
                print("Checkmate detected. Black wins!")
        elif self.board.is_stalemate('black') or self.board.is_stalemate('white'):
            self.game_over = True
            self.winner = 'Draw'
            if DEBUG:
                print("Stalemate detected. The game is a draw.")

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()

    # ---------- Sidebar, review, and analysis helpers ----------
    def handle_sidebar_click(self, pos):
        if self.btn_to_start.collidepoint(pos):
            self.go_to_start()
        elif self.btn_back.collidepoint(pos):
            self.step_back()
        elif self.btn_forward.collidepoint(pos):
            self.step_forward()
        elif self.btn_to_end.collidepoint(pos):
            self.go_to_end()
        elif self.btn_analyze.collidepoint(pos):
            self.analysis_enabled = not self.analysis_enabled
            self.analysis_result = None
            self.last_analyzed_ply = -1

    def step_back(self):
        mv = self.board.unmake_move(switch_turn=True)
        if mv:
            self.redo_stack.append(mv)
            self.in_review = True
            self._refresh_last_move_color()

    def step_forward(self):
        if self.redo_stack:
            mv = self.redo_stack.pop()
            sr, sc = mv['start_pos']
            er, ec = mv['end_pos']
            # Re-apply without validation; castling/promotions will be handled
            self.board.make_move(sr, sc, er, ec, switch_turn=True, validate=False)
        if not self.redo_stack:
            self.in_review = False
        self._refresh_last_move_color()

    def go_to_start(self):
        while True:
            mv = self.board.unmake_move(switch_turn=True)
            if not mv:
                break
            self.redo_stack.append(mv)
        self.in_review = True
        self._refresh_last_move_color()

    def go_to_end(self):
        while self.redo_stack:
            self.step_forward()
        self.in_review = False
        self._refresh_last_move_color()

    def coords_to_square(self, r, c):
        files = 'abcdefgh'
        return f"{files[c]}{8 - r}"

    def format_move(self, mv):
        piece = mv['piece']
        sr, sc = mv['start_pos']
        er, ec = mv['end_pos']
        cap = mv['captured_piece'] is not None
        pname = piece.name[0].upper() if piece.name != 'pawn' else ''
        sep = 'x' if cap else '-' 
        return f"{pname}{self.coords_to_square(sr, sc)}{sep}{self.coords_to_square(er, ec)}"

    def _refresh_last_move_color(self):
        if not self.board.move_history:
            self.last_move_color = None
        else:
            self.last_move_color = self.board.move_history[-1]['piece'].color

    def draw_icon_button(self, rect, icon, disabled=False):
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        base = self.UI_BUTTON if not disabled else (80, 80, 80)
        fill = self.UI_BUTTON_HOVER if hover and not disabled else base
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.UI_PANEL_BORDER, rect, 1, border_radius=8)
        cx = rect.x + rect.w // 2
        cy = rect.y + rect.h // 2
        size = 10
        color = self.UI_TEXT if not disabled else (180, 180, 180)
        if icon == 'first':
            pts = [(cx - size, cy), (cx - 2, cy - size), (cx - 2, cy + size)]
            pygame.draw.polygon(self.screen, color, pts)
            pygame.draw.rect(self.screen, color, (cx + 2, cy - size, 3, 2 * size))
        elif icon == 'prev':
            pts = [(cx + size//2, cy - size), (cx + size//2, cy + size), (cx - size, cy)]
            pygame.draw.polygon(self.screen, color, pts)
        elif icon == 'next':
            pts = [(cx - size//2, cy - size), (cx - size//2, cy + size), (cx + size, cy)]
            pygame.draw.polygon(self.screen, color, pts)
        elif icon == 'last':
            pts = [(cx + size, cy), (cx + 2, cy - size), (cx + 2, cy + size)]
            pygame.draw.polygon(self.screen, color, pts)
            pygame.draw.rect(self.screen, color, (cx - 5, cy - size, 3, 2 * size))

    def draw_pill_button(self, rect, label, on=False):
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        fill = self.UI_ACCENT_ON if on else self.UI_ACCENT
        if hover:
            fill = tuple(min(255, int(c * 1.08)) for c in fill)
        pygame.draw.rect(self.screen, fill, rect, border_radius=20)
        pygame.draw.rect(self.screen, self.UI_PANEL_BORDER, rect, 1, border_radius=20)
        text = self.small_font.render(label, True, (255, 255, 255))
        self.screen.blit(text, (rect.x + (rect.w - text.get_width()) // 2,
                                rect.y + (rect.h - text.get_height()) // 2))

    # draw_small_button removed (engine toggle no longer used)

    def draw_panel(self, rect, title=None):
        # Shadow
        shadow = pygame.Rect(rect.x + 2, rect.y + 3, rect.w, rect.h)
        srf = pygame.Surface((shadow.w, shadow.h), pygame.SRCALPHA)
        pygame.draw.rect(srf, (0, 0, 0, 60), srf.get_rect(), border_radius=12)
        self.screen.blit(srf, shadow.topleft)
        # Panel
        pygame.draw.rect(self.screen, self.UI_PANEL, rect, border_radius=12)
        pygame.draw.rect(self.screen, self.UI_PANEL_BORDER, rect, 1, border_radius=12)
        if title:
            title_text = self.small_font.render(title, True, self.UI_TEXT)
            self.screen.blit(title_text, (rect.x + 12, rect.y + 10))

    def draw_gradient_bar(self, x, y, w, h, top_color, bottom_color, radius=8):
        # Simple vertical gradient
        bar = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(h):
            t = i / max(1, h - 1)
            r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
            g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
            b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
            pygame.draw.line(bar, (r, g, b), (0, i), (w, i))
        # mask rounded corners by drawing onto a rounded rect clip
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
        bar.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        self.screen.blit(bar, (x, y))

    def ensure_analysis(self):
        if not self.analysis_enabled:
            return
        ply = len(self.board.move_history)
        if ply == self.last_analyzed_ply:
            return
        # Compute analysis using built-in engine only on a safe clone of the board
        side = self.board.current_turn
        ana_ai = AI(side)
        ana_ai.depth = max(5, self.analysis_depth)
        ana_ai.time_ms = 600
        # Search on a cloned board to guarantee no state mutations
        cloned = self.board.clone()
        best = ana_ai.get_move(cloned)
        if best:
            (sr, sc), (er, ec) = best
            best_str = f"{self.coords_to_square(sr, sc)}-{self.coords_to_square(er, ec)}"
        else:
            best_str = "(no move)"
        white_eval = -self.ai.evaluate_board(self.board)
        self.analysis_result = (best_str, white_eval)
        self.last_analyzed_ply = ply

    def draw_sidebar(self):
        x = self.board_pixels

        # Top controls panel
        ctrl_rect = pygame.Rect(x + 6, 6, self.sidebar_width - 12, 96)
        self.draw_panel(ctrl_rect)
        # Icon buttons row
        self.draw_icon_button(self.btn_to_start, 'first')
        self.draw_icon_button(self.btn_back, 'prev')
        self.draw_icon_button(self.btn_forward, 'next')
        self.draw_icon_button(self.btn_to_end, 'last')
        # Analysis toggle as pill
        self.draw_pill_button(self.btn_analyze, f"Analysis: {'ON' if self.analysis_enabled else 'OFF'}", on=self.analysis_enabled)

        # Mode chip (moved to second row to avoid overlap)
        mode = 'Review' if self.in_review else 'Live'
        chip_rect = self.live_chip_rect
        if chip_rect:
            pygame.draw.rect(self.screen, (90, 98, 110), chip_rect, border_radius=13)
            chip_text = self.tiny_font.render(mode, True, (255, 255, 255))
            self.screen.blit(chip_text, (chip_rect.x + (chip_rect.w - chip_text.get_width()) // 2,
                                         chip_rect.y + (chip_rect.h - chip_text.get_height()) // 2))

        # Evaluation panel
        eval_rect = pygame.Rect(x + 6, ctrl_rect.bottom + 8, self.sidebar_width - 12, 170)
        self.draw_panel(eval_rect, title='Evaluation')
        # Prefer analysis engine score if available
        self.ensure_analysis()
        if self.analysis_result:
            _, white_eval_val = self.analysis_result
            white_eval = white_eval_val if white_eval_val is not None else -self.ai.evaluate_board(self.board)
        else:
            white_eval = -self.ai.evaluate_board(self.board)
        score = max(-500, min(500, int(white_eval)))
        bar_h = 120
        bar_w = 28
        bar_x = eval_rect.x + 16
        bar_y = eval_rect.y + 36
        # Solid black/white evaluation bar (no gradient)
        # Outer border
        pygame.draw.rect(self.screen, (200, 200, 200), (bar_x, bar_y, bar_w, bar_h), 0, border_radius=10)
        # Inner area
        inner = pygame.Rect(bar_x + 2, bar_y + 2, bar_w - 4, bar_h - 4)
        pygame.draw.rect(self.screen, self.UI_PANEL_BORDER, inner, 0, border_radius=8)
        # Fill white top and black bottom based on score proportion
        white_portion = int((score + 500) / 1000 * inner.h)
        if white_portion > 0:
            pygame.draw.rect(self.screen, (245, 245, 245), (inner.x, inner.y, inner.w, white_portion))
        if inner.h - white_portion > 0:
            pygame.draw.rect(self.screen, (20, 20, 20), (inner.x, inner.y + white_portion, inner.w, inner.h - white_portion))
        # Marker line
        marker_y = inner.y + white_portion
        pygame.draw.rect(self.screen, (255, 215, 0), (inner.x - 3, max(inner.y, marker_y - 1), inner.w + 6, 2), border_radius=2)
        eval_text = self.small_font.render(f"White {score/100:.2f}", True, self.UI_TEXT)
        self.screen.blit(eval_text, (bar_x + bar_w + 12, bar_y))
        if self.analysis_result:
            best_str, _ = self.analysis_result
            best_text = self.small_font.render(f"Best: {best_str}", True, self.UI_TEXT)
            self.screen.blit(best_text, (bar_x + bar_w + 12, bar_y + 28))

        # Moves panel
        moves_rect = pygame.Rect(x + 6, eval_rect.bottom + 8, self.sidebar_width - 12, 800 - (eval_rect.bottom + 14))
        self.draw_panel(moves_rect, title='Moves')
        # Create move lines grouped by ply pairs (1. e2-e4 e7-e5)
        lines = []
        mh = self.board.move_history
        for i in range(0, len(mh), 2):
            num = i // 2 + 1
            wmv = self.format_move(mh[i]) if i < len(mh) else ''
            bmv = self.format_move(mh[i + 1]) if i + 1 < len(mh) else ''
            lines.append(f"{num}. {wmv}   {bmv}")
        # Scroll clamp
        max_visible = (moves_rect.h - 40) // 24
        max_offset = max(0, len(lines) - max_visible)
        self.move_scroll = max(0, min(self.move_scroll, max_offset))
        start = self.move_scroll
        end = min(len(lines), start + max_visible)
        y = moves_rect.y + 36
        # Alternating stripes and highlight last line
        last_line_index = (len(mh) - 1) // 2 if mh else -1
        for idx in range(start, end):
            row_rect = pygame.Rect(moves_rect.x + 8, y - 2, moves_rect.w - 16, 24)
            if idx % 2 == 0:
                pygame.draw.rect(self.screen, self.UI_STRIPE, row_rect, border_radius=6)
            if idx == last_line_index:
                pygame.draw.rect(self.screen, (70, 80, 100), row_rect, 2, border_radius=6)
            text = self.small_font.render(lines[idx], True, self.UI_TEXT)
            self.screen.blit(text, (moves_rect.x + 14, y))
            y += 24
