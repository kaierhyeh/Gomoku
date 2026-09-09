from config.game import BOARD_SIZE, EMPTY, BLACK, WHITE, WIN_LENGTH, MAX_CAPTURES

def in_bounds(row, col, holes):
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and (row, col) not in holes

def check_winner(captures, player):
    if captures[player] >= MAX_CAPTURES:
        return player
    return None

def has_five(board, row, col, player, holes):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        for sign in (1, -1):
            r, c = row + sign * dr, col + sign * dc
            while in_bounds(r, c, holes) and board[r][c] == player:
                count += 1
                r += sign * dr
                c += sign * dc
        if count >= WIN_LENGTH:
            return True
    return False

def get_five_cells_through(board, row, col, player, holes):
    """Return set of coordinates forming five-in-a-row through (row, col)."""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    cells = set()
    for dr, dc in directions:
        line_cells = [(row, col)]
        for sign in (1, -1):
            r, c = row + sign * dr, col + sign * dc
            while in_bounds(r, c, holes) and board[r][c] == player:
                line_cells.append((r, c))
                r += sign * dr
                c += sign * dc
        if len(line_cells) >= WIN_LENGTH:
            cells.update(line_cells)
    return cells

def has_any_five(board, player, holes):
    """Check if player has any sequence of 5 or more stones on the board."""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player and (r, c) not in holes:
                for dr, dc in directions:
                    pr, pc = r - dr, c - dc
                    if in_bounds(pr, pc, holes) and board[pr][pc] == player:
                        continue  # Not the start of a chain
                    count = 1
                    nr, nc = r + dr, c + dc
                    while in_bounds(nr, nc, holes) and board[nr][nc] == player:
                        count += 1
                        nr += dr
                        nc += dc
                    if count >= WIN_LENGTH:
                        return True
    return False

def would_capture(board, row, col, player, holes):
    """Check if placing a stone at (row, col) captures at least one opponent pair."""
    opponent = WHITE if player == BLACK else BLACK
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        for sign in (1, -1):
            r1, c1 = row + sign * dr, col + sign * dc
            r2, c2 = row + sign * 2 * dr, col + sign * 2 * dc
            r3, c3 = row + sign * 3 * dr, col + sign * 3 * dc
            if (in_bounds(r1, c1, holes) and in_bounds(r2, c2, holes) and in_bounds(r3, c3, holes)
                    and board[r1][c1] == opponent and board[r2][c2] == opponent and board[r3][c3] == player):
                return True
    return False

def is_double_free_three(board, row, col, player, holes):
    """
    Check if placing a stone at (row, col) creates two or more free-three alignments.
    Covers continuous free-threes and broken free-threes (_X_XX_ and _XX_X_).
    """
    board[row][col] = player
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    count = 0

    free_three_patterns = [
        (EMPTY, EMPTY, player, player, player, EMPTY),  # . . X X X .
        (EMPTY, player, EMPTY, player, player, EMPTY),  # . X . X X .
        (EMPTY, player, player, EMPTY, player, EMPTY),  # . X X . X .
        (EMPTY, player, player, player, EMPTY, EMPTY),  # . X X X . .
    ]

    for dr, dc in directions:
        line = []
        for i in range(-5, 6):
            r, c = row + i * dr, col + i * dc
            if in_bounds(r, c, holes):
                line.append((i, board[r][c]))
            else:
                line.append((i, -1))

        for start in range(len(line) - 5):
            window = line[start:start + 6]
            cells = tuple(cell for _, cell in window)
            if cells in free_three_patterns:
                if 0 in [offset for offset, cell in window if cell == player]:
                    count += 1
                    break

    board[row][col] = EMPTY
    return count >= 2
