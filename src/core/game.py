import random
from config.game import (BOARD_SIZE, EMPTY, BLACK, WHITE, HOLE, MAX_CAPTURES)
from config.bonus import (DECAY_LIFESPAN, POWER_BOMB, POWER_CROSS, POWER_DIAGONAL, STAR_MIN_PLY, STAR_MAX_PLY, STAR_WARN_PLY)
from rules.bonus import get_rules_for_mode
from rules.rules import in_bounds, check_winner, has_five, is_double_free_three

class Game:
    def __init__(self, rules=None, state=None, modifiers=None):
        from core.state import GameState
        from core.modifiers import DecayModifier, ShootingStarModifier, PowerModifier
        self.rules = rules if rules is not None else get_rules_for_mode("Standard")
        self.modifiers = modifiers if modifiers is not None else [DecayModifier(), ShootingStarModifier(), PowerModifier()]
        if state is None:
            self.state = GameState(rules=self.rules)
            self.state.next_star_ply = self._schedule_next_star() if self.rules.shooting_star else -1
        else:
            self.state = state

    @property
    def board(self): return self.state.board
    @board.setter
    def board(self, value): self.state.board = value
    @property
    def captures(self): return self.state.captures
    @captures.setter
    def captures(self, value): self.state.captures = value
    @property
    def individual_captures(self): return self.state.individual_captures
    @individual_captures.setter
    def individual_captures(self, value): self.state.individual_captures = value
    @property
    def ply_count(self): return self.state.ply_count
    @ply_count.setter
    def ply_count(self, value): self.state.ply_count = value
    @property
    def stones_ply(self): return self.state.stones_ply
    @stones_ply.setter
    def stones_ply(self, value): self.state.stones_ply = value
    @property
    def holes(self): return self.state.holes
    @holes.setter
    def holes(self, value): self.state.holes = value
    @property
    def hole_forecast(self): return self.state.hole_forecast
    @hole_forecast.setter
    def hole_forecast(self, value): self.state.hole_forecast = value
    @property
    def blipping_stones(self): return self.state.blipping_stones
    @blipping_stones.setter
    def blipping_stones(self, value): self.state.blipping_stones = value
    @property
    def next_star_ply(self): return self.state.next_star_ply
    @next_star_ply.setter
    def next_star_ply(self, value): self.state.next_star_ply = value
    @property
    def current_player(self): return self.state.current_player
    @current_player.setter
    def current_player(self, value): self.state.current_player = value
    @property
    def winner(self): return self.state.winner
    @winner.setter
    def winner(self, value): self.state.winner = value
    @property
    def last_move(self): return self.state.last_move
    @last_move.setter
    def last_move(self, value): self.state.last_move = value
    @property
    def history(self): return self.state.history
    @history.setter
    def history(self, value): self.state.history = value

    @property
    def render_hints(self):
        hints = {}
        for mod in self.modifiers:
            mod_hints = mod.get_render_hints(self.state)
            for pos, dict_hint in mod_hints.items():
                if pos not in hints:
                    hints[pos] = {}
                hints[pos].update(dict_hint)
        return hints

    def _save_state(self):
        self.history.append({
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
        })

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
        return True

    def _schedule_next_star(self):
        return self.ply_count + random.randint(STAR_MIN_PLY, STAR_MAX_PLY)

    def place_stone(self, row, col, player=None, power_type=None):
        if player is None: player = self.current_player
        if not self.is_valid_move(row, col, player): return False
        if hasattr(self, 'history'): self._save_state()

        for mod in self.modifiers:
            mod.on_turn_start(self, self.state)

        if (row, col) in self.holes:
            self.holes.remove((row, col))
            self.board[row][col] = EMPTY
            self.last_move = (row, col)
        else:
            self.board[row][col] = player
            self.last_move = (row, col)
            if self.rules.decay_enabled:
                self.stones_ply[(row, col)] = self.ply_count

            override = False
            for mod in self.modifiers:
                if mod.on_stone_placed(self, self.state, row, col, player, power_type):
                    override = True
                    break
            
            if not override:
                self._apply_captures(row, col, player)

        self.winner = self._check_winner(row, col, player)
        self.ply_count += 1

        if not self.winner:
            for mod in self.modifiers:
                mod.on_turn_end(self, self.state)
        
        self.current_player = WHITE if player == BLACK else BLACK
        return True

    def is_valid_move(self, row, col, player=None):
        if player is None: player = self.current_player
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE): return False
        if self.rules.shooting_star and (row, col) in self.holes: pass
        elif self.board[row][col] != EMPTY or (row, col) in self.hole_forecast: return False
        if self.rules.double_free_three and is_double_free_three(self.board, row, col, player, self.holes): return False
        return True

    def _apply_captures(self, row, col, player):
        opponent = WHITE if player == BLACK else BLACK
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            for sign in (1, -1):
                r1, c1 = row + sign * dr, col + sign * dc
                r2, c2 = row + sign * 2 * dr, col + sign * 2 * dc
                r3, c3 = row + sign * 3 * dr, col + sign * 3 * dc
                if (in_bounds(r1, c1, self.holes) and in_bounds(r2, c2, self.holes) and in_bounds(r3, c3, self.holes)
                        and self.board[r1][c1] == opponent and self.board[r2][c2] == opponent and self.board[r3][c3] == player):
                    self.board[r1][c1] = EMPTY
                    self.board[r2][c2] = EMPTY
                    if self.rules.decay_enabled:
                        self.stones_ply.pop((r1, c1), None)
                        self.stones_ply.pop((r2, c2), None)
                    self.captures[player] += 1
                    self.individual_captures[player] += 2

    def get_captures(self, player):
        return self.captures[player]

    def _check_winner(self, row, col, player):
        win = check_winner(self.captures, player)
        if win: return win
        if has_five(self.board, row, col, player, self.holes): return player
        return None

    def check_winner_after_captures(self, player):
        return self.captures[player] >= MAX_CAPTURES

    def is_hole(self, row, col):
        return (row, col) in self.holes

    def get_board(self):
        return self.board

    def is_game_over(self):
        return self.winner is not None

    def clone(self):
        from core.state import GameState
        new_state = GameState(
            rules=self.rules,
            board=[row[:] for row in self.state.board],
            captures=self.state.captures.copy(),
            individual_captures=self.state.individual_captures.copy(),
            holes=self.state.holes.copy(),
            hole_forecast=self.state.hole_forecast.copy(),
            blipping_stones=self.state.blipping_stones.copy(),
            next_star_ply=self.state.next_star_ply,
            ply_count=self.state.ply_count,
            stones_ply=self.state.stones_ply.copy(),
            current_player=self.state.current_player,
            winner=self.state.winner,
            last_move=self.state.last_move,
            history=[] # don't clone history for AI sim
        )
        return Game(self.rules, new_state)
