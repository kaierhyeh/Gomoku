"""
Gomoku Heuristic Evaluation Module
==================================

Overview
--------
This module provides static board evaluation and incremental move scoring for
the Gomoku AI engine. It models game mechanics including five-in-a-row victory
conditions, tactical line shapes (open fours, threes, twos), and Pente-style
pair capture mechanics (2-stone captures and 10-stone capture win).

Architecture & Workflow
-----------------------
1. Full-Board Static Evaluation (evaluate_board):
   - Minimax leaf evaluation: Computes AI_score - Opponent_score (zero-sum relative advantage).
   - Scans all 4 directions non-redundantly to aggregate sequence scores and captured pair bonuses.

2. Pattern Classification & Scoring (_score_sequence, _classify_pattern):
   - Maps continuous stone chains and open ends into heuristic pattern scores.
   - Evaluates: Five (1,000,000), Open Four (100,000), Closed Four (10,000),
     Open Three (5,000), Closed Three (500), Open Two (100), Closed Two (10).
   - Prunes dead patterns (both ends blocked) with score 0.

3. Capture Mechanics (_count_captures_for_scoring):
   - Checks 4 directions for sandwich capture patterns (player - opponent - opponent - player).
   - Tracks 2-stone pair removals and triggers instant victory upon reaching 5 pairs (10 stones).

4. Quick Move Scoring & Prioritization (quick_score_move):
   - Local O(1) radial evaluation around candidate move (row, col) for Alpha-Beta move ordering.
   - Tier 1 (10,000,000+): Current player instant win via five-in-a-row or 10-stone capture.
   - Tier 2 (5,000,000 - 7,000,000): Critical defense against opponent five-in-a-row or 10-stone capture win.
   - Tier 3 (< 1,000,000): Tactical combinations (open four, double three, forks) with 1.05x offensive weighting.

================================================================================
Gomoku 啟發式評估模組

概覽
--------
本模組提供五子棋 AI 引擎所需的靜態盤面評估（Static Board Evaluation）與
局部走步啟發式評分（Incremental Move Scoring）。邏輯涵蓋傳統五子連珠獲勝條件、
直線棋型（活四、衝四、活三、眠三、活二等），以及 Pente 規則中的夾吃機制
（夾吃 2 顆子與累計夾吃滿 10 顆子直接獲勝）。

架構與工作流程
--------------
1. 全盤靜態評估 (evaluate_board)：
   - Minimax 葉節點評估：計算 AI_score - Opponent_score（相對淨優勢）。
   - 沿四個方向向量進行不重複掃描，累加所有連續棋型分數與吃子獎勵。

2. 棋型辨識與評分 (_score_sequence, _classify_pattern)：
   - 依連續棋子長度與兩端開放狀態（open ends）映射為啟發式分數。
   - 分級評分：連五（1,000,000）、活四（100,000）、衝四（10,000）、
     活三（5,000）、眠三（500）、活二（100）、眠二（10）。
   - 兩端皆受阻之死棋型直接賦予 0 分。

3. 夾吃判定機制 (_count_captures_for_scoring)：
   - 檢查四個方向上的夾吃結構（我-敵-敵-我）。
   - 追蹤吃子進度，若累計夾吃滿 5 對（10 顆子）即達成夾吃獲勝條件。

4. 快速走步排序與分層優先權 (quick_score_move)：
   - 針對候選座標 (row, col) 進行 O(1) 局部輻射掃描，專供 Alpha-Beta 走步排序。
   - 第一層級 (10,000,000+)：我方連五或吃滿 10 顆直接絕殺。
   - 第二層級 (5,000,000 - 7,000,000)：對手即時獲勝威脅防守（防連五或防吃滿 10 顆）。
   - 第三層級 (< 1,000,000)：常規戰術棋型組合（活四、雙三等），包含 1.05x 進攻加權。
"""

from config.game import BOARD_SIZE, EMPTY, BLACK, WHITE, DIRECTIONS
from config.ai import SCORE


def evaluate_board(board, captures, player):
    """
    Full board heuristic evaluation from a given player's perspective.
    Input:
        1. board: The current game board.
        2. captures: A dictionary of captured stones for each player.
        3. player: The player for whom to evaluate the board.

    Return:
        AI_score - Opponent_score
    """
    opponent = WHITE if player == BLACK else BLACK
    ai_score = _score_player(board, player, captures.get(player, 0))
    opp_score = _score_player(board, opponent, captures.get(opponent, 0))
    return ai_score - opp_score


def _score_player(board, player, captured_pairs):
    """
    Sum up all pattern scores across all directions for a given player.

    Input:
        1. board: The current game board.
        2. player: The player whose stones are being evaluated.
        3. captured_pairs: Number of pairs already captured by this player.

    Return:
        Total heuristic score for the player.
    """
    total = 0

    # Bonus for captures already made (each pair captured is progress toward win)
    total += captured_pairs * 2000

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player:
                for dr, dc in DIRECTIONS:
                    # Only score starting from one end to avoid double counting
                    pr, pc = r - dr, c - dc
                    if 0 <= pr < BOARD_SIZE and 0 <= pc < BOARD_SIZE and board[pr][pc] == player:
                        continue  # Not the start of a sequence in this direction
                    total += _score_sequence(board, r, c, dr, dc, player)

    return total


def _score_sequence(board, row, col, dr, dc, player):
    """
    Analyze a single stone sequence starting at (row, col) in direction (dr, dc).
    Classifies and scores it based on pattern type.

    Input:
        1. board: The current game board.
        2. row: The starting row of the sequence.
        3. col: The starting column of the sequence.
        4. dr: Row direction increment (delta row).
        5. dc: Column direction increment (delta column).
        6. player: The player whose stones are being evaluated.

    Return:
        Heuristic score for the identified sequence pattern.
    """
    length = 0
    r, c = row, col

    # Count consecutive player stones
    while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
        length += 1
        r += dr
        c += dc

    # After the sequence, check if end is open or blocked
    end_open = (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == EMPTY)

    # Before the sequence, check if start is open or blocked
    br, bc = row - dr, col - dc
    start_open = (0 <= br < BOARD_SIZE and 0 <= bc < BOARD_SIZE and board[br][bc] == EMPTY)

    return _classify_pattern(length, start_open, end_open)


def _classify_pattern(length, start_open, end_open):
    """Map a sequence's length and openness to a heuristic score."""
    if length >= 5:
        return SCORE["FIVE"]

    both_open = start_open and end_open
    one_open = start_open ^ end_open   # XOR: exactly one end open

    if length == 4:
        return SCORE["OPEN_FOUR"] if both_open else (SCORE["CLOSED_FOUR"] if one_open else 0)
    if length == 3:
        return SCORE["OPEN_THREE"] if both_open else (SCORE["CLOSED_THREE"] if one_open else 0)
    if length == 2:
        return SCORE["OPEN_TWO"] if both_open else (SCORE["CLOSED_TWO"] if one_open else 0)

    return 0


def _count_captures_for_scoring(board, row, col, player):
    """Count number of opponent pairs captured by placing at (row, col)."""
    opponent = WHITE if player == BLACK else BLACK
    pairs = 0
    for dr, dc in DIRECTIONS:
        for sign in (1, -1):
            r1, c1 = row + sign * dr, col + sign * dc
            r2, c2 = row + sign * 2 * dr, col + sign * 2 * dc
            r3, c3 = row + sign * 3 * dr, col + sign * 3 * dc
            if (0 <= r1 < BOARD_SIZE and 0 <= c1 < BOARD_SIZE and
                0 <= r2 < BOARD_SIZE and 0 <= c2 < BOARD_SIZE and
                0 <= r3 < BOARD_SIZE and 0 <= c3 < BOARD_SIZE and
                board[r1][c1] == opponent and board[r2][c2] == opponent and board[r3][c3] == player):
                pairs += 1
    return pairs


def quick_score_move(board, row, col, player, captures):
    """
    Lightweight evaluation of placing a stone at (row, col)
    Used for move ordering before full Minimax recursion.

    Input:
        1. board: The current game board.
        2. row: The row of the move.
        3. col: The column of the move.
        4. player: The player placing the stone.
        5. captures: A dictionary of captured stones for each player.

    Return:
        Combined score for the player and opponent (to rank candidate moves).
    """
    opponent = WHITE if player == BLACK else BLACK
    score = 0

    # 1. Offensive capture bonus (Immediate win if reaching 5 pairs)
    my_caps = _count_captures_for_scoring(board, row, col, player)
    if captures.get(player, 0) + my_caps >= 5:
        return SCORE["FIVE"] * 10  # Immediate win by 10 captures!
    score += my_caps * 25000

    # Defensive capture blocking
    # 2. Defensive capture blocking (Urgent defense if opponent could reach 5 pairs)
    opp_caps = _count_captures_for_scoring(board, row, col, opponent)
    if captures.get(opponent, 0) + opp_caps >= 5:
        score += SCORE["OPEN_FOUR"] * 2  # Must block opponent 10-capture win!
    else:
        score += opp_caps * 20000
    opp_win_by_capture = (captures.get(opponent, 0) + opp_caps >= 5)

    # 3. Line scan in all 4 directions
    player_max_line = 0
    opp_max_line = 0
    player_line_sum = 0
    opp_line_sum = 0

    for dr, dc in DIRECTIONS:
        score += _scan_line_score(board, row, col, dr, dc, player)
        score += _scan_line_score(board, row, col, dr, dc, opponent) * 1.05
        p_score = _scan_line_score(board, row, col, dr, dc, player)
        o_score = _scan_line_score(board, row, col, dr, dc, opponent)

        if p_score > player_max_line:
            player_max_line = p_score
        if o_score > opp_max_line:
            opp_max_line = o_score

        player_line_sum += p_score
        opp_line_sum += o_score

    # Tier 1: Immediate win for current player (5-in-a-row)
    # Absolute highest priority (10,000,000+), trumps all defensive threats
    if player_max_line >= SCORE["FIVE"]:
        return SCORE["FIVE"] * 10 + opp_line_sum

    # Tier 2: Opponent immediate win threat (5-in-a-row or 10-capture win)
    # Second highest priority (5,000,000 - 7,000,000)
    if opp_max_line >= SCORE["FIVE"] or opp_win_by_capture:
        score += SCORE["FIVE"] * 5

    if not opp_win_by_capture:
        score += opp_caps * 20000

    # Tier 3: Positional line combinations (below 1,000,000)
    score += int(player_line_sum * 1.05) + opp_line_sum

    return score


def _scan_line_score(board, row, col, dr, dc, player):
    """
    Count consecutive player stones in one direction through (row, col)
    with open-end validation.
    """
    count = 1
    open_ends = 0

    for sign in (1, -1):
        r, c = row + sign * dr, col + sign * dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
            count += 1
            r += sign * dr
            c += sign * dc
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == EMPTY:
            open_ends += 1

    if count >= 5:
        return SCORE["FIVE"]
    if count == 4:
        if open_ends == 2:
            return SCORE["OPEN_FOUR"]
        elif open_ends == 1:
            return SCORE["CLOSED_FOUR"]
        return 0  # Dead four (cannot form five)
    if count == 3:
        if open_ends == 2:
            return SCORE["OPEN_THREE"]
        elif open_ends == 1:
            return SCORE["CLOSED_THREE"]
        return 0  # Dead three
    if count == 2:
        if open_ends == 2:
            return SCORE["OPEN_TWO"]
        elif open_ends == 1:
            return SCORE["CLOSED_TWO"]
        return 0  # Dead two
    return 1 if open_ends > 0 else 0
