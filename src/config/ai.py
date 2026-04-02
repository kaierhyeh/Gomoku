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
