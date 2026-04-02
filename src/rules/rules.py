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

def is_double_free_three(board, row, col, player, holes):
    board[row][col] = player
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    count = 0
    for dr, dc in directions:
        line = []
        for i in range(-4, 5):
            r, c = row + i * dr, col + i * dc
            if in_bounds(r, c, holes):
                line.append((i, board[r][c]))
            else:
                line.append((i, -1))
        
        for start in range(len(line) - 4):
            window = line[start:start + 5]
            cells = [cell for _, cell in window]
            if (cells.count(player) == 3 and cells.count(EMPTY) == 2 
                and cells[0] == EMPTY and cells[4] == EMPTY 
                and 0 in [i for i, cell in window if cell == player]):
                count += 1
                break
    board[row][col] = EMPTY
    return count >= 2
