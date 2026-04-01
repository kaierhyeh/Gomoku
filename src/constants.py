# ──────────────────────────────────────────────
# Constants for the Gomoku project
# ──────────────────────────────────────────────

# Board
BOARD_SIZE = 19          # 19x19 Go board
EMPTY = 0
BLACK = 1                # Human player (default) or AI
WHITE = 2                # AI (default) or second human
HOLE = 3                 # Star mode hole

# Win conditions
WIN_LENGTH = 5           # Five or more in a row to win
MAX_CAPTURES = 5         # 5 captured pairs (10 stones) = win

# Game Modes
MODE_STANDARD = "Standard"
MODE_DECAY    = "Decay"
MODE_POWER    = "Power"
MODE_STAR     = "Star"
MODE_LIMITLESS = "Standard Unlimited"
MODE_EVERYTHING = "Everything"

# ──────────────────────────────────────────────
# GUI constants
# ──────────────────────────────────────────────
WINDOW_WIDTH  = 900
WINDOW_HEIGHT = 720
BOARD_MARGIN  = 40       # Pixels from window edge to first line
CELL_SIZE     = 34       # Pixels between grid lines

# Colors (R, G, B)
COLOR_BG         = (220, 179, 92)    # Wood-tone board background
COLOR_LINE       = (80, 50, 20)      # Grid lines
COLOR_BLACK_STONE = (20, 20, 20)
COLOR_WHITE_STONE = (240, 240, 240)
COLOR_HIGHLIGHT  = (255, 80, 80, 160)  # Hover / suggestion indicator
COLOR_PANEL_BG   = (40, 30, 20)
COLOR_TEXT       = (230, 220, 200)
COLOR_ACCENT     = (200, 130, 50)

# ──────────────────────────────────────────────
# Bonus Modes constants
# ──────────────────────────────────────────────
# Decay
DECAY_LIFESPAN       = 20   # Total ply a stone survives (= 10 of its owner's turns)
DECAY_WARN_THRESHOLD = 6    # Show countdown timer when ply_remaining <= this
DECAY_CRACK_THRESHOLD = 2   # Draw crack lines when ply_remaining <= this

# Power Stones
POWER_UNLOCK_THRESHOLD = 5  # Capture 5 individual stones to gain a power
POWER_BOMB     = "Bomb"
POWER_CROSS    = "Cross"
POWER_DIAGONAL = "Diagonal"

# Shooting Star
STAR_MIN_PLY = 5
STAR_MAX_PLY = 12
STAR_WARN_PLY = 3           # Show forecast 3 ply before hole forms

# ──────────────────────────────────────────────
AI_TIME_LIMIT    = 0.45   # Maximum seconds per move (hard cap)
MAX_DEPTH        = 10     # Minimum search depth required by Subject
NEIGHBOR_RADIUS  = 2      # Only consider empty cells within this radius of existing stones

# Heuristic pattern scores
SCORE = {
    "FIVE":         1_000_000,
    "OPEN_FOUR":      100_000,
    "CLOSED_FOUR":     10_000,
    "OPEN_THREE":       5_000,
    "CLOSED_THREE":       500,
    "OPEN_TWO":           100,
    "CLOSED_TWO":          10,
}
