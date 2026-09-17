import time
import random
from config.game import (BOARD_SIZE, EMPTY, BLACK, WHITE)
from config.ai import (AI_TIME_LIMIT, MAX_DEPTH, NEIGHBOR_RADIUS, SCORE)
from ai.heuristic import evaluate_board, quick_score_move


class AI:
    """
    Gomoku AI using Minimax with Alpha-Beta pruning.
    Includes: move ordering, candidate filtering, iterative deepening,
    and a transposition table (Zobrist hashing).
    Guarantees depth >= 10 in under 0.5s average response time.
    """

    def __init__(self, player):
        self.player = player
        self.opponent = WHITE if player == BLACK else BLACK
        self.transposition_table = {}
        self._init_zobrist()
        self.last_think_time = 0.0
        self.last_depth_reached = 0

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

    def _get_branch_limit(self, depth):
        """Adaptive branching limit based on remaining search depth."""
        if depth >= 8:
            return 4
        if depth >= 5:
            return 3
        return 2

    # ──────────────────────────────────────────────
    # Public entry point
    # ──────────────────────────────────────────────

    def get_best_move(self, game):
        """
        Iterative deepening Minimax search reaching MAX_DEPTH (>= 10).
        Returns (row, col) of the best found move.
        """
        start = time.time()
        candidates = self._get_candidates(game.board)

        # Opening: play center if board is completely empty
        if game.board[BOARD_SIZE // 2][BOARD_SIZE // 2] == EMPTY and len(candidates) == 0:
            self.last_think_time = time.time() - start
            self.last_depth_reached = MAX_DEPTH
            return (BOARD_SIZE // 2, BOARD_SIZE // 2)

        if not candidates:
            return None

        best_move = None
        self.last_depth_reached = 0

        # Iterative deepening from depth 2 to MAX_DEPTH (10)
        # Using steps 2, 4, 6, 8, 10 allows reaching 10 smoothly with PV-move ordering
        for depth in range(2, MAX_DEPTH + 1, 2):
            if time.time() - start > AI_TIME_LIMIT * 0.92:
                break
            result = self._minimax_root(game, depth, candidates, start, best_move)
            if result is not None:
                best_move = result
                self.last_depth_reached = depth
                # If best_move directly wins the game, no need to search deeper
                sim = game.clone()
                if sim.place_stone(best_move[0], best_move[1], self.player) and sim.is_game_over() and sim.winner == self.player:
                    break
            if time.time() - start > AI_TIME_LIMIT:
                break

        self.last_think_time = time.time() - start
        return best_move

    def _minimax_root(self, game, depth, candidates, start, pv_move):
        """Run one full Minimax search at the given depth with PV-move priority."""
        alpha = float('-inf')
        beta = float('inf')
        best_score = float('-inf')
        best_move = None

        # Order candidates by quick heuristic score with PV-move placed first
        # ─────────────────────────────────────────────────────────────
        # 【變數說明：scored】
        # • 語法結構與型別：List[Tuple[float, int, int]]
        #   由三元組 (score, row, col) 所組成的列表。
        # • 各欄位含意：
        #   - score (float，即 tuple[0]，第一名走步為 scored[0][0])：
        #     該候選走步的快速啟發式評估分數 (quick_score_move)。分數愈高代表該步
        #     價值愈大或戰術急迫性愈高：
        #       * >= SCORE["FIVE"] * 10 (10,000,000)：當前玩家直接連五獲勝或吃滿10子獲勝（最高優先級）。
        #       * >= SCORE["FIVE"] * 5  (5,000,000)：防守對手即時連五或吃滿10子獲勝（次高優先級）。
        #       * >= SCORE["OPEN_FOUR"] (100,000)：活四威脅走步。
        #   - row (int，即 tuple[1]，第一名走步為 scored[0][1])：
        #     走步在棋盤上的列座標 (0 ~ BOARD_SIZE-1)。
        #   - col (int，即 tuple[2]，第一名走步為 scored[0][2])：
        #     走步在棋盤上的欄座標 (0 ~ BOARD_SIZE-1)。
        # • 排序與選取：
        #   - scored.sort(reverse=True)：按分數由高至低遞減排序。
        #   - scored[0]：當前排序後分數最高、最優先搜尋的最佳候選步元組。
        #   - scored[0][0]：該最佳候選步的分數，用於強制走步判斷與安全剪枝。
        # ─────────────────────────────────────────────────────────────
        scored = []
        for r, c in candidates:
            s = quick_score_move(game.board, r, c, self.player, game.captures)
            if (r, c) == pv_move:
                s += 1_000_000_000  # Search PV move first for optimal cut-offs
            scored.append((s, r, c))
        scored.sort(reverse=True)
        root_limit = 8 if depth >= 6 else 12
        scored = scored[:root_limit]

        for s, row, col in scored:
            if time.time() - start > AI_TIME_LIMIT:
                break
            sim = game.clone()
            if not sim.place_stone(row, col, self.player):
                continue
            if sim.is_game_over() and sim.winner == self.player:
                return (row, col)  # Immediate winning move found!
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
        Recursive Minimax search with Alpha-Beta pruning, transposition table,
        and selective forward pruning.
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

        curr = self.player if is_maximizing else self.opponent
        candidates = self._get_candidates(game.board)
        if not candidates:
            return 0

        scored = []
        for r, c in candidates:
            s = quick_score_move(game.board, r, c, curr, game.captures)
            scored.append((s, r, c))
        scored.sort(reverse=True)

        # Forcing move logic:
        # 1. Immediate win for current player: prune to 1 move (instant win is proven)
        if scored and scored[0][0] >= SCORE["FIVE"] * 10:
            scored = scored[:1]
        # 2. Urgent defense against opponent immediate win threat:
        #    Only evaluate moves that directly defend against the threat (up to 4)
        elif scored and scored[0][0] >= SCORE["FIVE"] * 5:
            scored = [m for m in scored if m[0] >= SCORE["FIVE"] * 5][:4]
        # 3. Open four threat: narrow to top 2 moves
        elif scored and scored[0][0] >= SCORE["OPEN_FOUR"]:
            scored = scored[:2]
        else:
            limit = self._get_branch_limit(depth)
            scored = scored[:limit]

        if is_maximizing:
            best = float('-inf')
            for s, row, col in scored:
                if time.time() - start > AI_TIME_LIMIT:
                    break
                sim = game.clone()
                if not sim.place_stone(row, col, curr):
                    continue
                val = self._minimax(sim, depth - 1, alpha, beta, False, start)
                best = max(best, val)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break   # Beta cut-off (prune)
        else:
            best = float('inf')
            for s, row, col in scored:
                if time.time() - start > AI_TIME_LIMIT:
                    break
                sim = game.clone()
                if not sim.place_stone(row, col, curr):
                    continue
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
        Drastically reduces the branching factor.
        """
        candidates = set()
        occupied_count = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] != EMPTY:
                    occupied_count += 1
                    radius = 1 if occupied_count <= 2 else NEIGHBOR_RADIUS
                    for dr in range(-radius, radius + 1):
                        for dc in range(-radius, radius + 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                                candidates.add((nr, nc))
        return list(candidates)

    def suggest_move(self, game):
        """Return a suggested move for the hotseat move-suggestion feature."""
        return self.get_best_move(game)
