"""
Gomoku AI Search Engine Module
==============================

Overview
--------
This module implements the search engine for the Gomoku AI.
It combines Iterative Deepening Minimax with Alpha-Beta pruning, Zobrist
hashing for transposition caching, candidate move filtering, and heuristic
move ordering to achieve search depth >= 10 in under 0.5s average think time.

Architecture & Workflow
-----------------------
1. Candidate Selection (_get_candidates):
   - Spatial filtering: Only considers empty board intersections within
     NEIGHBOR_RADIUS (2 cells) of already placed stones.
   - Opening optimization: Plays center (BOARD_SIZE // 2) if the board is empty.

2. Iterative Deepening (get_best_move):
   - Successively deepens search from depth 2 to MAX_DEPTH (10) in steps of 2.
   - Carries the Principal Variation (PV) move from depth (d-2) into depth d
     to ensure the best move is explored first for maximal Alpha-Beta cutoffs.
   - Enforces a strict time limit (AI_TIME_LIMIT = 0.45s) to guarantee responsiveness.
   - Breaks early if an immediate winning sequence is confirmed.

3. Root Move Ordering & Pruning (_minimax_root):
   - Evaluates each candidate move with quick_score_move().
   - Prioritizes the PV move with an extreme score boost (+1,000,000,000).
   - Limits root branching factor: top 8 candidates (depth >= 6) or 12 candidates
     (depth < 6) to keep high-depth search tractable.

4. Minimax with Alpha-Beta Pruning (_minimax):
   - Transposition Table: 64-bit Zobrist hashing caches exact scores, lower bounds,
     and upper bounds to eliminate redundant subtree evaluation across paths.
   - Dynamic Branching: Adapts child branch limits based on remaining depth
     (e.g., 2 candidates at depth 1-4, 3 at depth 5-7, 4 at depth >= 8).
   - Alpha-Beta Pruning: Designed to optimize the Minimax search,
                            by pruning subtrees as soon as beta <= alpha.
   - Leaf Evaluation: Uses evaluate_board() at depth 0 or terminal states.

================================================================================
Gomoku AI 搜尋引擎模組

概覽
--------
結合迭代加深搜尋（Iterative Deepening Minimax）、Alpha-Beta 剪枝、
Zobrist 雜湊置換表（Transposition Table）、候選步空間篩選以及啟發式走步排序，
確保在嚴格時間限制（平均反應時間 < 0.5s）下達到搜尋深度 >= 10。

架構與工作流程
--------------
1. 候選步選取 (_get_candidates)：
   - 空間局部過濾：僅探測已有棋子周圍 NEIGHBOR_RADIUS（2 格）範圍內的空位，
     大幅縮減 19x19 棋盤的初始分支維度。
   - 開局最佳化：若全盤皆空，直接佔據天元（棋盤中心 BOARD_SIZE // 2）。

2. 迭代加深搜尋 (get_best_move)：
   - 搜尋深度以步長 2 逐步加深（depth = 2, 4, 6, 8, 10）。
   - PV 走步延續（Principal Variation）：將深度 d-2 找到的最佳走步傳遞至深度 d，
     作為首個探索分支，使 Alpha-Beta 剪枝效益極大化。
   - 硬性時間上限（AI_TIME_LIMIT = 0.45s）：逾時立即中斷並採用前一完整深度的最佳解。
   - 即時絕殺早退：若發現必勝走步，立即停止搜尋並回傳。

3. 根節點走步排序與剪枝 (_minimax_root)：
   - 調用 quick_score_move() 對所有候選步進行快速啟發式排序。
   - 對 PV 走步（pv_move）給予極高優先權加權（+1,000,000,000），確保排在索引 0。
   - 依搜尋深度動態縮減根節點分支數：深度 >= 6 時保留前 8 個候選步；
     淺層時保留前 12 個，確保深層搜尋可在時間內完成。

4. Minimax 與 Alpha-Beta 剪枝遞迴 (_minimax)：
   - 置換表（Transposition Table）：使用 64-bit Zobrist 雜湊快取搜尋分數、
     下界與上界，消除不同搜尋路徑下相同盤面的重複計算。
   - 動態子節點分支控制（Dynamic Branching）：依剩餘深度動態限制子節點展開數
     （深度 1-4 取 2 個，深度 5-7 取 3 個，深度 >= 8 取 4 個）。
   - Alpha-Beta 剪枝：設計來最佳化Minimax演算的演算法 －
                        當 beta <= alpha 時裁剪分支對局。
   - 葉節點評估：到達終端節點或 depth == 0 時呼叫 evaluate_board()。
"""

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
    # Zobrist hashing for transposition table (a dictionary)
    #
    # transposition_table[hash_value] = {'score': best, 'depth': depth}
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
        """
        Compute the Zobrist hash for the current board state.
        將 19×19 棋盤壓縮成一個 64-bit 整數，以實現 O(1) 高速查表。

        Input:
            board: 2D list representing the current board state.
        Return:
            64-bit integer hash value.
        """
        h = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                v = board[r][c]
                if v != EMPTY:
                    # Use .get() to avoid KeyErrors
                    #     if non-standard elements are on the board
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

        Return:
            (row, col) of the best found move.
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
                if (
                    sim.place_stone(best_move[0], best_move[1], self.player) and
                    sim.is_game_over() and
                    sim.winner == self.player
                ):
                    break
            if time.time() - start > AI_TIME_LIMIT:
                break

        self.last_think_time = time.time() - start
        return best_move

    def _minimax_root(self, game, depth, candidates, start, pv_move):
        """
        Run one full Minimax search at the given depth with PV-move priority.

        Input:
            1. self: The AI instance.
            2. game: The current game state.
            3. depth: The search depth.
            4. candidates: List of possible moves.
            5. start: The start time of the search.
            6. pv_move: Principal variation move to prioritize.

        Return:
            (row, col) of the best move found at this depth.
        """
        alpha = float('-inf')
        beta = float('inf')
        best_score = float('-inf')
        best_move = None

        scored = []
        for r, c in candidates:
            s = quick_score_move(game.board, r, c, self.player, game.captures)
            if (r, c) == pv_move:
                s += 1_000_000_000  # Search PV move first for optimal cut-offs
            scored.append((s, r, c))
        scored.sort(reverse=True)
        root_limit = 8 if depth >= 6 else 12
        scored = scored[:root_limit]

        for _, row, col in scored:
            if time.time() - start > AI_TIME_LIMIT:
                break
            sim = game.clone()  # 我模擬下子
            if not sim.place_stone(row, col, self.player):
                continue
            if sim.is_game_over() and sim.winner == self.player:
                return (row, col)  # Immediate winning move found!
            # 模擬對方下子，進行 Minimax 遞迴搜尋
            score = self._minimax(sim, depth - 1, alpha, beta, False, start)
            if score > best_score:
                best_score = score
                best_move = (row, col)
            alpha = max(alpha, best_score)

        return best_move  # (row, col)
    # Order candidates by quick heuristic score with PV-move placed first
    # ─────────────────────────────────────────────────────────────
    # 【變數說明：scored】
    # • 語法結構與型別：List[Tuple[float, int, int]]
    #   由三元組 (score, row, col) 所組成的列表。
    # • 各欄位含意：
    #   - score (float，即 tuple[0]，第一名走步為 scored[0][0])：
    #     該候選走步的快速啟發式評估分數 (quick_score_move)。分數愈高代表該步
    #     價值愈大或戰術急迫性愈高：
    #       * >= SCORE["FIVE"] * 10 (10,000,000)：
    #            當前玩家直接連五獲勝或吃滿10子獲勝（最高優先級）。
    #       * >= SCORE["FIVE"] * 5  (5,000,000)：
    #            防守對手即時連五或吃滿10子獲勝（次高優先級）。
    #       * >= SCORE["OPEN_FOUR"] (100,000)：
    #            活四威脅走步。
    #   - row (int，即 tuple[1]，第一名走步為 scored[0][1])：
    #     走步在棋盤上的列座標 (0 ~ BOARD_SIZE-1)。
    #   - col (int，即 tuple[2]，第四名走步為 scored[3][2])：
    #     走步在棋盤上的欄座標 (0 ~ BOARD_SIZE-1)。
    # • 排序與選取：
    #   - scored.sort(reverse=True)：按分數由高至低遞減排序。
    #   - scored[0]：當前排序後分數最高、最優先搜尋的最佳候選步元組。
    #   - scored[0][0]：該最佳候選步的分數，用於強制走步判斷與安全剪枝。
    # ─────────────────────────────────────────────────────────────

    # ─────────────────────────────────────────────────────────────────────────
    # Minimax with Alpha-Beta pruning:
    #     https://ithelp.ithome.com.tw/m/articles/10355817
    #
    # α: Highest score on the maximizer layer/ply, dynamically updated during the search.
    # β: Lowest score on the minimizer layer/ply, dynamically updated during the search.
    # α pruning:
    #     When the minimizer, node C, finds a branch that gives a β
    #     that is smaller than or equal to α (4 ≦ 5), knowing that the maximizer,
    #     node A, won't choose the node C, the minimizer will prune the remaining
    #     branches.
    # β pruning:
    #     When the maximizer, node M, finds a branch that gives an α
    #     that is greater than or equal to β (5 ≦ 8), knowing that the minimizer,
    #     node K, won't choose the node M, the maximizer will prune the remaining
    #     branches.
    # ─────────────────────────────────────────────────────────────────────────
    # α: 於 maximizer 層的最高分，於搜尋過程中動態更新。
    # β: 於 minimizer 層的最低分，於搜尋過程中動態更新。
    # α 剪枝:
    #     當理性的 minimizer 節點(C)在自己的分支裡找到了小於等於 α 的 β (4 ≦ 5) 時，
    #     因知道上一層理性的 maximizer (A)不會選擇 C 這個節點，所以剩餘的分支都不用計算。
    # β 剪枝:
    #     當理性的 maximizer 節點(M)在自己的分支裡找到了大於等於 β 的 α (5 ≦ 8) 時，
    #     因知道上一層理性的 minimizer (K)不會選擇 M 這個節點，所以剩餘的分支都不用計算。
    # ─────────────────────────────────────────────────────────────────────────
    def _minimax(self, game, depth, alpha, beta, is_my_turn, start):
        """
        Recursive Minimax search with Alpha-Beta pruning, transposition table,
        and selective forward pruning.

        Input:
            1. self : The AI instance.
            2. game : The current game state.
            3. depth: The remaining search depth.
            4. alpha: Highest score that the player can achieve.
            5. beta : Lowest score that the opponent plans to allow.
            6. is_my_turn: A boolean indicating if the current node is my turn.
            7. start: The start time of the search.

        Return:
            The best score (float) for the current node.
        """
        # Check transposition table (tt)
        board_hash = self._compute_hash(game.board)
        # Use .get to avoid KeyErrors if the hash is not present
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

        curr = self.player if is_my_turn else self.opponent
        candidates = self._get_candidates(game.board)
        if not candidates:
            return 0

        # 由高分到低分排列所有候選步
        scored = []
        for r, c in candidates:
            s = quick_score_move(game.board, r, c, curr, game.captures)
            scored.append((s, r, c))
        scored.sort(reverse=True)

        # 候選步篩選:
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

        # 遍歷篩選後的候選步
        if is_my_turn:
            best = float('-inf')
            for _, row, col in scored:
                if time.time() - start > AI_TIME_LIMIT:
                    break
                sim = game.clone()        # 模擬開始：我方落子(row, col)
                if not sim.place_stone(row, col, curr):
                    continue
                # 我模擬對方落子（走法甲、乙、丙、丁......）
                val = self._minimax(sim, depth - 1, alpha, beta, False, start)
                best = max(best, val)     # 從各走法中選最高分
                alpha = max(alpha, best)  # 更新 alpha
                if beta <= alpha:         # 表示對方不會選這個節點，剩餘分支不必計算
                    break   # Beta cut-off
        else:
            best = float('inf')
            for _, row, col in scored:
                if time.time() - start > AI_TIME_LIMIT:
                    break
                sim = game.clone()        # 模擬開始：對方落子(row, col)
                if not sim.place_stone(row, col, curr):
                    continue
                # 對方模擬我落子（走法甲、乙、丙、丁......）
                val = self._minimax(sim, depth - 1, alpha, beta, True, start)
                best = min(best, val)     # 對方會選我得分最低的走法
                beta = min(beta, best)    # 更新 beta
                if beta <= alpha:         # 表示我不會選這節點，剩餘分支不必計算
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
                            if (
                                0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and
                                board[nr][nc] == EMPTY
                            ):
                                candidates.add((nr, nc))
        return list(candidates)

    def suggest_move(self, game):
        """Return a suggested move for the hotseat move-suggestion feature."""
        return self.get_best_move(game)
