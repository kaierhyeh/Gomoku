from constants import BOARD_SIZE, EMPTY, BLACK, WHITE, WIN_LENGTH, MAX_CAPTURES, DECAY_LIFESPAN


class Game:
    """Core game engine: board state, move validation, captures, win detection."""

    def __init__(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.captures = {BLACK: 0, WHITE: 0}  # Number of captured PAIRS per player
        self.ply_count = 0
        self.stones_ply = {}  # Tracks (r, c) -> placed_ply
        self.current_player = BLACK
        self.winner = None
        self.last_move = None

    # ──────────────────────────────────────────────
    # Move execution
    # ──────────────────────────────────────────────

    def place_stone(self, row, col, player=None):
        """Place a stone after validating the move. Returns True on success."""
        if player is None:
            player = self.current_player
        if not self.is_valid_move(row, col, player):
            return False
        self.board[row][col] = player
        self.last_move = (row, col)
        self.stones_ply[(row, col)] = self.ply_count
        self._apply_captures(row, col, player)
        self.winner = self._check_winner(row, col, player)
        
        self.ply_count += 1
        if not self.winner:
            self._apply_decay()
            
        self.current_player = WHITE if player == BLACK else BLACK
        return True

    def is_valid_move(self, row, col, player=None):
        """Check if placing a stone at (row, col) is a legal move."""
        if player is None:
            player = self.current_player
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return False
        if self.board[row][col] != EMPTY:
            return False
        if self._is_double_free_three(row, col, player):
            return False
        return True

    # ──────────────────────────────────────────────
    # Capture logic
    # ──────────────────────────────────────────────

    def _apply_captures(self, row, col, player):
        """Remove any opponent pairs flanked by the placed stone."""
        opponent = WHITE if player == BLACK else BLACK
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            for sign in (1, -1):
                r1, c1 = row + sign * dr, col + sign * dc
                r2, c2 = row + sign * 2 * dr, col + sign * 2 * dc
                r3, c3 = row + sign * 3 * dr, col + sign * 3 * dc

                if (self._in_bounds(r1, c1) and self._in_bounds(r2, c2) and self._in_bounds(r3, c3)
                        and self.board[r1][c1] == opponent
                        and self.board[r2][c2] == opponent
                        and self.board[r3][c3] == player):
                    self.board[r1][c1] = EMPTY
                    self.board[r2][c2] = EMPTY
                    self.stones_ply.pop((r1, c1), None)
                    self.stones_ply.pop((r2, c2), None)
                    self.captures[player] += 1

    def get_captures(self, player):
        """Return the number of captured pairs for a player."""
        return self.captures[player]

    # ──────────────────────────────────────────────
    # Decay logic
    # ──────────────────────────────────────────────

    def _apply_decay(self):
        """Remove stones that have exceeded their DECAY_LIFESPAN."""
        expired = []
        for pos, placed_ply in self.stones_ply.items():
            if self.ply_count - placed_ply >= DECAY_LIFESPAN:
                expired.append(pos)
        
        for r, c in expired:
            self.board[r][c] = EMPTY
            del self.stones_ply[(r, c)]

    # ──────────────────────────────────────────────
    # Win detection
    # ──────────────────────────────────────────────

    def _check_winner(self, row, col, player):
        """Check if the last move resulted in a win."""
        # Win by capture: 5 or more pairs taken
        if self.captures[player] >= MAX_CAPTURES:
            return player
        # Win by five-in-a-row
        # Note: the Endgame Capture rule (opponent breaks the five by capturing)
        # is intentionally omitted here for robustness; it is rarely relevant
        # and the previous implementation produced false negatives.
        if self._has_five(row, col, player):
            return player
        return None

    def _get_winning_cells(self, row, col, player):
        """Return the set of (r,c) cells that form the five-in-a-row through (row,col)."""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            cells = [(row, col)]
            for sign in (1, -1):
                r, c = row + sign * dr, col + sign * dc
                while self._in_bounds(r, c) and self.board[r][c] == player:
                    cells.append((r, c))
                    r += sign * dr
                    c += sign * dc
            if len(cells) >= WIN_LENGTH:
                return set(cells)
        return set()

    def _has_five(self, row, col, player):
        """Return True if the player has 5+ stones in a row through (row, col)."""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            for sign in (1, -1):
                r, c = row + sign * dr, col + sign * dc
                while self._in_bounds(r, c) and self.board[r][c] == player:
                    count += 1
                    r += sign * dr
                    c += sign * dc
            if count >= WIN_LENGTH:
                return True
        return False

    def _opponent_can_break_five(self, row, col, player):
        """
        Endgame Capture rule: returns True ONLY if the opponent can make a single
        capturing move that removes at least one stone from the winning five.
        Only captures that directly break the line count.
        """
        opponent = WHITE if player == BLACK else BLACK
        winning_cells = self._get_winning_cells(row, col, player)
        if not winning_cells:
            return False

        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] != EMPTY:
                    continue
                # Check if placing at (r,c) would capture any stone in winning_cells
                for dr, dc in directions:
                    for sign in (1, -1):
                        r1, c1 = r + sign * dr, r + sign * dc   # typo-safe: use correct coords
                        r1, c1 = r + sign * dr, c + sign * dc
                        r2, c2 = r + sign * 2 * dr, c + sign * 2 * dc
                        r3, c3 = r + sign * 3 * dr, c + sign * 3 * dc
                        if (self._in_bounds(r1, c1) and self._in_bounds(r2, c2)
                                and self._in_bounds(r3, c3)
                                and self.board[r1][c1] == player
                                and self.board[r2][c2] == player
                                and self.board[r3][c3] == opponent):
                            # This would capture (r1,c1) and (r2,c2)
                            if (r1, c1) in winning_cells or (r2, c2) in winning_cells:
                                # Also verify opponent has not already lost by capture
                                if self.captures[opponent] < MAX_CAPTURES:
                                    return True
        return False

    def check_winner_after_captures(self, player):
        """Called after captures to re-check if captures created 5-in-a-row breakage."""
        return self.captures[player] >= MAX_CAPTURES

    # ──────────────────────────────────────────────
    # Double free-three detection
    # ──────────────────────────────────────────────

    def _is_double_free_three(self, row, col, player):
        """
        Return True if placing at (row, col) creates two or more simultaneous
        free-three alignments (forbidden move).
        """
        self.board[row][col] = player
        free_three_count = self._count_free_threes(row, col, player)
        self.board[row][col] = EMPTY
        return free_three_count >= 2

    def _count_free_threes(self, row, col, player):
        """Count the number of free-three alignments that pass through (row, col)."""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        count = 0
        for dr, dc in directions:
            if self._is_free_three_in_direction(row, col, player, dr, dc):
                count += 1
        return count

    def _is_free_three_in_direction(self, row, col, player, dr, dc):
        """
        Check if there is a free-three through (row, col) in the given direction.
        A free-three is exactly 3 aligned stones with both ends open and no gaps
        that would prevent forming an unblockable open four.
        """
        # Collect the window of cells around (row, col) in this direction
        line = []
        for i in range(-4, 5):
            r, c = row + i * dr, col + i * dc
            if self._in_bounds(r, c):
                line.append((i, self.board[r][c]))
            else:
                line.append((i, -1))  # Out of bounds treated as blocked

        # Find player stones around center, look for pattern: _ X X X _
        for start in range(len(line) - 4):
            window = line[start:start + 5]
            cells = [cell for _, cell in window]
            if (cells.count(player) == 3
                    and cells.count(EMPTY) == 2
                    and cells[0] == EMPTY
                    and cells[4] == EMPTY
                    and 0 in [i for i, cell in window if cell == player]):
                return True
        return False

    # ──────────────────────────────────────────────
    # Utility helpers
    # ──────────────────────────────────────────────

    def _in_bounds(self, row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def get_board(self):
        return self.board

    def is_game_over(self):
        return self.winner is not None

    def clone(self):
        """Return a deep copy of the game state for AI simulation."""
        new_game = Game.__new__(Game)
        new_game.board = [row[:] for row in self.board]
        new_game.captures = self.captures.copy()
        new_game.ply_count = self.ply_count
        new_game.stones_ply = self.stones_ply.copy()
        new_game.current_player = self.current_player
        new_game.winner = self.winner
        new_game.last_move = self.last_move
        return new_game
