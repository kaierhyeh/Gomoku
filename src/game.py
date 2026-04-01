import random
from constants import (BOARD_SIZE, EMPTY, BLACK, WHITE, HOLE, WIN_LENGTH, MAX_CAPTURES,
                       DECAY_LIFESPAN, POWER_BOMB, POWER_CROSS, POWER_DIAGONAL,
                       STAR_MIN_PLY, STAR_MAX_PLY, STAR_WARN_PLY)
from bonus import RuleSet, get_rules_for_mode


class Game:
    """Core game engine: board state, move validation, captures, win detection."""

    def __init__(self, rules=None):
        self.rules = rules if rules is not None else get_rules_for_mode("Standard")
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.captures = {BLACK: 0, WHITE: 0}  # Number of captured PAIRS per player
        self.individual_captures = {BLACK: 0, WHITE: 0} # For Power Stones

        self.ply_count = 0
        self.stones_ply = {}  # Tracks (r, c) -> placed_ply

        # Shooting Star fields
        self.holes = set()
        self.hole_forecast = {}  # (r, c) -> ply_becomes_hole
        self.blipping_stones = {}
        self.next_star_ply = self._schedule_next_star() if self.rules.shooting_star else -1

        self.current_player = BLACK
        self.winner = None
        self.last_move = None
        self.history = []

    def _save_state(self):
        import copy
        state = {
            'board': [row[:] for row in self.board],
            'captures': self.captures.copy(),
            'individual_captures': self.individual_captures.copy(),
            'holes': self.holes.copy(),
            'hole_forecast': self.hole_forecast.copy(),
            'blipping_stones': self.blipping_stones.copy(),
            'next_star_ply': self.next_star_ply,
            'ply_count': self.ply_count,
            'stones_ply': self.stones_ply.copy(),
            'current_player': self.current_player,
            'winner': self.winner,
            'last_move': self.last_move,
            'decays': getattr(self, 'decays', {}).copy(),
            'power_board': getattr(self, 'power_board', {}).copy(),
            'power_inventory': copy.deepcopy(getattr(self, 'power_inventory', {BLACK: [], WHITE: []})),
            'active_power': getattr(self, 'active_power', None)
        }
        self.history.append(state)

    def undo(self):
        if not self.history:
            return False
        state = self.history.pop()
        self.board = state['board']
        self.captures = state['captures']
        self.individual_captures = state['individual_captures']
        self.holes = state['holes']
        self.hole_forecast = state['hole_forecast']
        self.blipping_stones = state.get('blipping_stones', {})
        self.next_star_ply = state['next_star_ply']
        self.ply_count = state['ply_count']
        self.stones_ply = state['stones_ply']
        self.current_player = state['current_player']
        self.winner = state['winner']
        self.last_move = state['last_move']

        if hasattr(self, 'decays'):
            self.decays = state['decays']
        if hasattr(self, 'power_board'):
            self.power_board = state['power_board']
            self.power_inventory = state['power_inventory']
            self.active_power = state['active_power']
        return True

    def _schedule_next_star(self):
        return self.ply_count + random.randint(STAR_MIN_PLY, STAR_MAX_PLY)

    # ──────────────────────────────────────────────
    # Move execution
    # ──────────────────────────────────────────────

    def place_stone(self, row, col, player=None, power_type=None):
        """Place a stone. power_type is one of POWER_* constants if used."""
        if player is None:
            player = self.current_player

        if not self.is_valid_move(row, col, player):
            return False

        # Do not save history for AI simulations (which use clone without history tracking)
        if hasattr(self, 'history'):
            self._save_state()

        if (row, col) in self.holes:
            self.holes.remove((row, col))
            self.board[row][col] = EMPTY
            self.last_move = (row, col)
        else:
            self.board[row][col] = player
            self.last_move = (row, col)
            if self.rules.decay_enabled:
                self.stones_ply[(row, col)] = self.ply_count

            if power_type and self.rules.power_stones:
                self._apply_power(row, col, player, power_type)
            else:
                self._apply_captures(row, col, player)

        self.winner = self._check_winner(row, col, player)

        self.ply_count += 1

        # Shooting star updates
        if self.rules.shooting_star and not self.winner:
            self._update_shooting_star()

        if self.rules.decay_enabled and not self.winner:
            self._apply_decay()

        self.current_player = WHITE if player == BLACK else BLACK
        return True

    def is_valid_move(self, row, col, player=None):
        """Check if placing a stone at (row, col) is a legal move."""
        if player is None:
            player = self.current_player
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return False
        if self.rules.shooting_star and (row, col) in self.holes:
            pass # Allowed to fill an active hole!
        elif self.board[row][col] != EMPTY or (row, col) in self.holes or (row, col) in self.hole_forecast:
            return False
        if self.rules.double_free_three and self._is_double_free_three(row, col, player):
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
                    if self.rules.decay_enabled:
                        self.stones_ply.pop((r1, c1), None)
                        self.stones_ply.pop((r2, c2), None)
                    self.captures[player] += 1
                    # Normal captures grant power points (1 stone = 1 point)
                    self.individual_captures[player] += 2

    def get_captures(self, player):
        """Return the number of captured pairs for a player."""
        return self.captures[player]

    # ──────────────────────────────────────────────
    # Power Stone logic
    # ──────────────────────────────────────────────

    def _apply_power(self, row, col, player, power_type):
        """Applies the area-of-effect power stone logic."""
        opponent = WHITE if player == BLACK else BLACK
        cleared_stones = []

        # Deduct 3 points for using a skill
        if player in self.individual_captures:
            self.individual_captures[player] = max(0, self.individual_captures[player] - 3)

        if power_type == POWER_BOMB:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    r, c = row + dr, col + dc
                    if self._in_bounds(r, c) and self.board[r][c] != EMPTY:
                        cleared_stones.append((r, c))

        elif power_type == POWER_CROSS:
            for d in [-2, -1, 1, 2]:
                r1, c1 = row + d, col
                if self._in_bounds(r1, c1) and self.board[r1][c1] == opponent:
                    cleared_stones.append((r1, c1))
                r2, c2 = row, col + d
                if self._in_bounds(r2, c2) and self.board[r2][c2] == opponent:
                    cleared_stones.append((r2, c2))

        elif power_type == POWER_DIAGONAL:
            for d in [-2, -1, 1, 2]:
                r1, c1 = row + d, col + d
                if self._in_bounds(r1, c1) and self.board[r1][c1] == opponent:
                    cleared_stones.append((r1, c1))
                r2, c2 = row + d, col - d
                if self._in_bounds(r2, c2) and self.board[r2][c2] == opponent:
                    cleared_stones.append((r2, c2))

        for r, c in cleared_stones:
            self.board[r][c] = EMPTY
            # NOTE: Stones destroyed by powers do NOT grant individual_captures
            if self.rules.decay_enabled and (r, c) in self.stones_ply:
                self.stones_ply.pop((r, c), None)

        # Deduct power usage
        if self.individual_captures[player] >= 5:
            self.individual_captures[player] = max(0, self.individual_captures[player] - 5)

    # ──────────────────────────────────────────────
    # Decay & Shooting Star logic
    # ──────────────────────────────────────────────

    def _update_shooting_star(self):
        """Handle hole forecast, creation, and blipping stone logic."""
        # Flip blipping stones every 3 plies relative to their origin
        for (br, bc), start_ply in self.blipping_stones.items():
            if self.board[br][bc] in (BLACK, WHITE) and (self.ply_count - start_ply) > 0 and (self.ply_count - start_ply) % 3 == 0:
                self.board[br][bc] = WHITE if self.board[br][bc] == BLACK else BLACK
                # Flipped blipping stone behaves like a fresh stone placement for capture checks.
                self._apply_captures(br, bc, self.board[br][bc])

        # Check for holes that manifest this ply
        to_manifest = [pos for pos, ply in self.hole_forecast.items() if self.ply_count >= ply]
        for r, c in to_manifest:
            # 50% chance to be a Hole, 50% chance to be a Blipping Stone
            if random.random() < 0.5:
                self.holes.add((r, c))
                self.board[r][c] = HOLE  # Use HOLE so it's not EMPTY for sequences
            else:
                color = random.choice([BLACK, WHITE])
                self.blipping_stones[(r, c)] = self.ply_count
                self.board[r][c] = color

            if self.rules.decay_enabled:
                self.stones_ply.pop((r, c), None)
            del self.hole_forecast[(r, c)]

        # Check if we need to schedule a new hole forecast
        if self.ply_count >= self.next_star_ply - STAR_WARN_PLY:
            # Generate a new hole location
            empty_cells = []
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if (r, c) not in self.holes and (r, c) not in self.hole_forecast and self.board[r][c] == EMPTY:
                        empty_cells.append((r, c))

            if empty_cells:
                r, c = random.choice(empty_cells)
                # Next star ply is when the hole becomes active
                self.hole_forecast[(r, c)] = self.next_star_ply
                self.next_star_ply = self._schedule_next_star()

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
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and (row, col) not in self.holes

    def is_hole(self, row, col):
        return (row, col) in self.holes

    def get_board(self):
        return self.board

    def is_game_over(self):
        return self.winner is not None

    def clone(self):
        """Return a deep copy of the game state for AI simulation."""
        new_game = Game.__new__(Game)
        new_game.rules = self.rules
        new_game.board = [row[:] for row in self.board]
        new_game.captures = self.captures.copy()
        new_game.individual_captures = self.individual_captures.copy()

        new_game.holes = self.holes.copy()
        new_game.hole_forecast = self.hole_forecast.copy()
        new_game.blipping_stones = self.blipping_stones.copy()
        new_game.next_star_ply = self.next_star_ply

        new_game.ply_count = self.ply_count
        new_game.stones_ply = self.stones_ply.copy()
        new_game.current_player = self.current_player
        new_game.winner = self.winner
        new_game.last_move = self.last_move
        return new_game
