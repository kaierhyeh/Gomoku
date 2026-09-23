from config.game import BOARD_SIZE, EMPTY, BLACK, WHITE, DIRECTIONS, WIN_LENGTH


def in_bounds(row, col, holes):
    """Check if (row, col) is valid: within the board and not in holes."""
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and (row, col) not in holes


def has_five(board, row, col, player, holes):
    """Check if placing a stone at (row, col) creates a five-in-a-row."""
    for dr, dc in DIRECTIONS:  # (dr, dc) = (0, 1), (1, 0), (1, 1), (1, -1)
        count = 1
        for sign in (1, -1):  # sign = 1, -1
            r, c = row + sign * dr, col + sign * dc
            while in_bounds(r, c, holes) and board[r][c] == player:
                count += 1
                r += sign * dr
                c += sign * dc
        if count >= WIN_LENGTH:
            return True
    return False


def get_five_cells_through(board, row, col, player, holes):
    """Return the five-in-a-row coordinates set in (row, col)."""
    cells = set()
    for dr, dc in DIRECTIONS:
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
    """
    Check if player has any sequence of 5 or more stones on the board.
    Attention: "Endgame Capture rule" - Can opponent break it
    """
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player and (r, c) not in holes:
                for dr, dc in DIRECTIONS:
                    pr, pc = r - dr, c - dc
                    if in_bounds(pr, pc, holes) and board[pr][pc] == player:
                        continue  # Skip, not the start of a chain
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
    for dr, dc in DIRECTIONS:
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
    board[row][col] = player  # 下子模擬
    count = 0

    free_three_patterns = [
        (EMPTY, EMPTY, player, player, player, EMPTY),  # _ _ X X X _
        (EMPTY, player, EMPTY, player, player, EMPTY),  # _ X _ X X _
        (EMPTY, player, player, EMPTY, player, EMPTY),  # _ X X _ X _
        (EMPTY, player, player, player, EMPTY, EMPTY),  # _ X X X _ _
    ]

    for dr, dc in DIRECTIONS:
        line = []
        # 從某方向正反採樣各五格
        for i in range(-5, 6):  # range(start, exclusive stop): -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5
            r, c = row + i * dr, col + i * dc
            if in_bounds(r, c, holes):
                line.append((i, board[r][c]))
            else:
                line.append((i, -1))

        for start in range(len(line) - 5):
            window = line[start:start + 6]
            cells = tuple(cell for _, cell in window)  # 把 iterator 的 i 拿掉，只留棋子資訊
            if cells in free_three_patterns:
                if 0 in [offset for offset, cell in window if cell == player]:
                    count += 1
                    break

    board[row][col] = EMPTY  # 復原落子
    return count >= 2

# start in range(6): 0, 1, 2, 3, 4, 5
# window = line[start:start + 6]    (line[start:exclusive stop])
# 組合成為 ↓
# start=0：
#     window = line[-5:1]   -5 ~ 0
# start=1：
#     window = line[-4:2]   -4 ~ 1
# start=2：
#     window = line[-3:3]   -3 ~ 2
# start=3：
#     window = line[-2:4]   -2 ~ 3
# start=4：
#     window = line[-1:5]   -1 ~ 4
# start=5：
#     window = line[0:6]     0 ~ 5

# [offset for offset, cell in window if cell == player]:
# 遍歷 window(offset, cell) 的每個元素，
# 並檢查 cell 是否為 player (玩家棋子，排除邊界與空格)，
# 如果是，則將對應的 offset 加入結果列表。
#         window:
#         ┌─────────────────────────────────┐
#  offset │  -3   -2   -1   [0]    1    2   │  (長度 6)
#   cell  │   _    _    X   [X]    X    _   │
#         └─────────────────────────────────┘
#                            ▲ 新落子正好是其中一顆

# • 提取實體棋子 offsets: [-1, 0, 1]
# • 判定 0 in [-1, 0, 1]  ──>  True！新落子【0】確實是三顆 X 之一，成功計入一條活三！
# > 為什麼新落子是 0?
# > 因為我們一開始「從某方向正反採樣各五格」，是以落子為中心。
