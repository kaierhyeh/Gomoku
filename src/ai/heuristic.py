from config.game import BOARD_SIZE, EMPTY, BLACK, WHITE
from config.ai import SCORE


# ──────────────────────────────────────────────
# Direction vectors for scanning (horizontal, vertical, diagonals)
# ──────────────────────────────────────────────
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]


def evaluate_board(board, captures, player):
    """
    Full board heuristic evaluation from a given player's perspective.
    Returns: AI_score - Opponent_score
    Combined offense + defense scoring.
    """
    opponent = WHITE if player == BLACK else BLACK
    ai_score = _score_player(board, player, captures.get(player, 0))
    opp_score = _score_player(board, opponent, captures.get(opponent, 0))
    return ai_score - opp_score


def _score_player(board, player, captured_pairs):
    """Sum up all pattern scores across all directions for a given player."""
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
    Lightweight evaluation of placing a stone at (row, col).
    Used for move ordering before full Minimax recursion.
    Returns: combined score for the player and opponent (to rank candidate moves).
    """
    opponent = WHITE if player == BLACK else BLACK
    score = 0

    # Offensive capture bonus
    # 1. Offensive capture bonus (Immediate win if reaching 5 pairs)
    my_caps = _count_captures_for_scoring(board, row, col, player)
    if captures.get(player, 0) + my_caps >= 5:
        return SCORE["FIVE"]  # Immediate win by 10 captures!
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
    """Count consecutive player stones in one direction through (row, col) with open-end validation."""
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
