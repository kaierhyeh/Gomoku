from typing import Dict, Any, Tuple
from core.state import GameState
from config.bonus import DECAY_LIFESPAN, DECAY_WARN_THRESHOLD, DECAY_CRACK_THRESHOLD, STAR_MIN_PLY, STAR_MAX_PLY, STAR_WARN_PLY, POWER_BOMB, POWER_CROSS, POWER_DIAGONAL
from config.game import EMPTY, BLACK, WHITE, HOLE, BOARD_SIZE
import random

class GameModifier:
    def on_turn_start(self, game: 'Game', state: GameState):
        pass

    def on_stone_placed(self, game: 'Game', state: GameState, row: int, col: int, player: int, power_type: str = None) -> bool:
        """Return True if this modifier overrides normal stone placement."""
        return False

    def on_turn_end(self, game: 'Game', state: GameState):
        pass

    def get_render_hints(self, state: GameState) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """Return a mapping of (row, col) to dictionary of drawing hints."""
        return {}

class DecayModifier(GameModifier):
    def on_turn_end(self, game: 'Game', state: GameState):
        if not game.rules.decay_enabled: return
        expired = []
        for (r, c), ply_placed in state.stones_ply.items():
            if state.ply_count - ply_placed >= DECAY_LIFESPAN:
                expired.append((r, c))
        for (r, c) in expired:
            state.board[r][c] = EMPTY
            del state.stones_ply[(r, c)]

    def get_render_hints(self, state: GameState) -> Dict[Tuple[int, int], Dict[str, Any]]:
        hints = {}
        if not state.rules.decay_enabled: return hints
        for (r, c), ply_placed in state.stones_ply.items():
            rem = DECAY_LIFESPAN - (state.ply_count - ply_placed)
            if rem <= DECAY_WARN_THRESHOLD:
                if (r, c) not in hints: hints[(r, c)] = {}
                hints[(r, c)]["age_label"] = str(rem)
            if rem <= DECAY_CRACK_THRESHOLD:
                if (r, c) not in hints: hints[(r, c)] = {}
                hints[(r, c)]["cracked"] = True
        return hints

class ShootingStarModifier(GameModifier):
    def on_turn_end(self, game: 'Game', state: GameState):
        if not game.rules.shooting_star: return

        # Flip blipping stones every 3 plies relative to their origin
        for (br, bc), start_ply in list(state.blipping_stones.items()):
            if state.board[br][bc] in (BLACK, WHITE) and (state.ply_count - start_ply) > 0 and (state.ply_count - start_ply) % 3 == 0:
                state.board[br][bc] = WHITE if state.board[br][bc] == BLACK else BLACK
                # Flipped blipping stone behaves like a fresh stone placement for capture checks.
                game._apply_captures(br, bc, state.board[br][bc])

        # Check for holes that manifest this ply
        to_manifest = [pos for pos, ply in state.hole_forecast.items() if state.ply_count >= ply]
        for r, c in to_manifest:
            # 50% chance to be a Hole, 50% chance to be a Blipping Stone
            if random.random() < 0.5:
                state.holes.add((r, c))
                state.board[r][c] = HOLE  # Use HOLE so it's not EMPTY for sequences
            else:
                color = random.choice([BLACK, WHITE])
                state.blipping_stones[(r, c)] = state.ply_count
                state.board[r][c] = color

            if game.rules.decay_enabled:
                state.stones_ply.pop((r, c), None)
            del state.hole_forecast[(r, c)]

        # Generate new hole forecast if needed
        if state.next_star_ply == -1:
            state.next_star_ply = state.ply_count + random.randint(STAR_MIN_PLY, STAR_MAX_PLY)

        if state.ply_count >= state.next_star_ply - STAR_WARN_PLY:
            # Generate a new hole location
            empty_cells = []
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if (r, c) not in state.holes and (r, c) not in state.hole_forecast and state.board[r][c] == EMPTY:
                        empty_cells.append((r, c))

            if empty_cells:
                r, c = random.choice(empty_cells)
                # Next star ply is when the hole becomes active
                state.hole_forecast[(r, c)] = state.next_star_ply
                state.next_star_ply = state.ply_count + random.randint(STAR_MIN_PLY, STAR_MAX_PLY)

    def get_render_hints(self, state: GameState) -> Dict[Tuple[int, int], Dict[str, Any]]:
        hints = {}
        if not state.rules.shooting_star: return hints
        for (r, c), start_ply in state.blipping_stones.items():
            if state.board[r][c] in (BLACK, WHITE):
                rem = 3 - ((state.ply_count - start_ply) % 3)
                if (r, c) not in hints: hints[(r, c)] = {}
                hints[(r, c)]["blip"] = True
                hints[(r, c)]["age_label"] = str(rem)

        for (r, c), target_ply in state.hole_forecast.items():
            rem = max(1, min(3, target_ply - state.ply_count))
            if (r, c) not in hints: hints[(r, c)] = {}
            hints[(r, c)]["hole_forecast"] = rem
        return hints

class PowerModifier(GameModifier):
    def on_stone_placed(self, game: 'Game', state: GameState, row: int, col: int, player: int, power_type: str = None) -> bool:
        if not game.rules.power_stones or not power_type: return False

        opponent = WHITE if player == BLACK else BLACK
        cleared = []

        # Bomb / Cross / Diagonal logic copied from _apply_power
        if power_type == POWER_BOMB:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    r, c = row+dr, col+dc
                    if 0<=r<19 and 0<=c<19 and state.board[r][c] != EMPTY:
                        cleared.append((r,c))
        elif power_type == POWER_CROSS:
            for d in [-2,-1,1,2]:
                for r, c in [(row+d, col), (row, col+d)]:
                    if 0<=r<19 and 0<=c<19 and state.board[r][c] == opponent:
                        cleared.append((r,c))
        elif power_type == POWER_DIAGONAL:
            for d in [-2,-1,1,2]:
                for r, c in [(row+d, col+d), (row+d, col-d)]:
                    if 0<=r<19 and 0<=c<19 and state.board[r][c] == opponent:
                        cleared.append((r,c))

        for r, c in cleared:
            state.board[r][c] = EMPTY
            if (r,c) in state.stones_ply:
                del state.stones_ply[(r,c)]

        if state.individual_captures[player] >= 5:
            state.individual_captures[player] = max(0, state.individual_captures[player] - 5)

        return True # Handled placement
