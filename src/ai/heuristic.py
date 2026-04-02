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
    opponent = WHITE if player == BLACK else BLACK
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


def quick_score_move(board, row, col, player, captures):
    """
    Lightweight evaluation of placing a stone at (row, col).
    Used for move ordering before full Minimax recursion.
    Returns: combined score for the player and opponent (to rank candidate moves).
    """
    opponent = WHITE if player == BLACK else BLACK
    score = 0

    for dr, dc in DIRECTIONS:
        # Offensive: how this move improves our sequences
        score += _scan_line_score(board, row, col, dr, dc, player)
        # Defensive: how this move blocks the opponent
        score += _scan_line_score(board, row, col, dr, dc, opponent) * 0.9

    return score


def _scan_line_score(board, row, col, dr, dc, player):
    """Count consecutive player stones in one direction through (row, col)."""
    count = 1
    for sign in (1, -1):
        r, c = row + sign * dr, col + sign * dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
            count += 1
            r += sign * dr
            c += sign * dc

    # Return exponential score based on length
    if count >= 5:
        return SCORE["FIVE"]
    if count == 4:
        return SCORE["OPEN_FOUR"]
    if count == 3:
        return SCORE["OPEN_THREE"]
    if count == 2:
        return SCORE["OPEN_TWO"]
    return 1
