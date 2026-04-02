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
