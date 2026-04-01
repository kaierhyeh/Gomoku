import time
import random
from constants import (BOARD_SIZE, EMPTY, BLACK, WHITE,
                       AI_TIME_LIMIT, MAX_DEPTH, NEIGHBOR_RADIUS, SCORE)
from heuristic import evaluate_board, quick_score_move


class AI:
    """
    Gomoku AI using Minimax with Alpha-Beta pruning.
    Includes: move ordering, candidate filtering, iterative deepening,
    and a transposition table (Zobrist hashing).
    """

    def __init__(self, player):
        self.player = player
        self.opponent = WHITE if player == BLACK else BLACK
        self.transposition_table = {}
        self._init_zobrist()
        self.last_think_time = 0.0

    # ──────────────────────────────────────────────
    # Zobrist hashing for transposition table
    # ──────────────────────────────────────────────

    def _init_zobrist(self):
        """Initialize random 64-bit keys for each (row, col, color) combination."""
        rng = random.Random(42)
        self.zobrist_table = {
            (r, c, color): rng.getrandbits(64)
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            for color in (1, 2, 3, 4, 5)
        }

    def _compute_hash(self, board):
        h = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                v = board[r][c]
                if v != EMPTY:
                    # Use .get() to avoid KeyErrors if non-standard elements are on the board
                    h ^= self.zobrist_table.get((r, c, v), 0)
        return h

    # ──────────────────────────────────────────────
    # Public entry point
    # ──────────────────────────────────────────────

    def get_best_move(self, game):
        """
        Iterative deepening Minimax search.
        Searches depth 2, 3, 4, ... until the time limit is reached.
        Returns (row, col) of the best found move.
        """
        start = time.time()
        best_move = None
        candidates = self._get_candidates(game.board)

        if not candidates:
            return None

        # Opening: play center if board is empty
        if game.board[BOARD_SIZE // 2][BOARD_SIZE // 2] == EMPTY:
            self.last_think_time = time.time() - start
            return (BOARD_SIZE // 2, BOARD_SIZE // 2)

        for depth in range(2, MAX_DEPTH + 1):
            if time.time() - start > AI_TIME_LIMIT * 0.8:
                break
            result = self._minimax_root(game, depth, candidates, start)
            if result is not None:
                best_move = result
            if time.time() - start > AI_TIME_LIMIT:
                break

        self.last_think_time = time.time() - start
        return best_move

    def _minimax_root(self, game, depth, candidates, start):
        """Run one full Minimax search at the given depth. Returns the best (row, col)."""
        alpha = float('-inf')
        beta = float('inf')
        best_score = float('-inf')
        best_move = None

        # Order candidates by quick heuristic score (descending) for better pruning
        ordered = sorted(
            candidates,
            key=lambda m: quick_score_move(game.board, m[0], m[1], self.player, game.captures),
            reverse=True
        )

        for row, col in ordered:
            if time.time() - start > AI_TIME_LIMIT:
                break
            sim = game.clone()
            sim.place_stone(row, col, self.player)
            score = self._minimax(sim, depth - 1, alpha, beta, False, start)
            if score > best_score:
                best_score = score
                best_move = (row, col)
            alpha = max(alpha, best_score)

        return best_move

    # ──────────────────────────────────────────────
    # Minimax with Alpha-Beta pruning
    # ──────────────────────────────────────────────

    def _minimax(self, game, depth, alpha, beta, is_maximizing, start):
        """
        Recursive Minimax search with Alpha-Beta pruning.
        - alpha: best score the maximizer (AI) can guarantee so far
        - beta:  best score the minimizer (opponent) can guarantee so far
        - Prune when beta <= alpha (this branch cannot improve the result)
        """
        # Check transposition table
        board_hash = self._compute_hash(game.board)
        tt_entry = self.transposition_table.get(board_hash)
        if tt_entry and tt_entry['depth'] >= depth:
            return tt_entry['score']

        # Terminal conditions
        if game.is_game_over():
            winner = game.winner
            if winner == self.player:
                return SCORE["FIVE"] + depth   # Prefer quicker wins
            elif winner == self.opponent:
                return -(SCORE["FIVE"] + depth)
            return 0

        if depth == 0 or time.time() - start > AI_TIME_LIMIT:
            return evaluate_board(game.board, game.captures, self.player)

        candidates = self._get_candidates(game.board)
        current = self.player if is_maximizing else self.opponent

        # Move ordering: evaluate quick scores before recursing
        candidates = sorted(
            candidates,
            key=lambda m: quick_score_move(game.board, m[0], m[1], current, game.captures),
            reverse=is_maximizing
        )

        if is_maximizing:
            best = float('-inf')
            for row, col in candidates:
                sim = game.clone()
                sim.place_stone(row, col, current)
                val = self._minimax(sim, depth - 1, alpha, beta, False, start)
                best = max(best, val)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break   # Beta cut-off (prune)
        else:
            best = float('inf')
            for row, col in candidates:
                sim = game.clone()
                sim.place_stone(row, col, current)
                val = self._minimax(sim, depth - 1, alpha, beta, True, start)
                best = min(best, val)
                beta = min(beta, best)
                if beta <= alpha:
                    break   # Alpha cut-off (prune)

        # Store in transposition table
        self.transposition_table[board_hash] = {'score': best, 'depth': depth}
        return best

    # ──────────────────────────────────────────────
    # Candidate move generation
    # ──────────────────────────────────────────────

    def _get_candidates(self, board):
        """
        Return a list of candidate (row, col) positions to consider.
        Only empty cells within NEIGHBOR_RADIUS of an existing stone are included.
        This drastically reduces the branching factor from 361 to ~20-40.
        """
        candidates = set()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] != EMPTY:
                    for dr in range(-NEIGHBOR_RADIUS, NEIGHBOR_RADIUS + 1):
                        for dc in range(-NEIGHBOR_RADIUS, NEIGHBOR_RADIUS + 1):
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE
                                    and board[nr][nc] == EMPTY):
                                candidates.add((nr, nc))
        return list(candidates)

    def suggest_move(self, game):
        """Return a suggested move for the hotseat move-suggestion feature."""
        return self.get_best_move(game)
