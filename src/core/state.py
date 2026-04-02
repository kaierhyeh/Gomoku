from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, List, Optional
from config.game import BOARD_SIZE, EMPTY, BLACK, WHITE

@dataclass
class GameState:
    rules: any
    board: List[List[int]] = field(default_factory=lambda: [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)])
    captures: Dict[int, int] = field(default_factory=lambda: {BLACK: 0, WHITE: 0})
    individual_captures: Dict[int, int] = field(default_factory=lambda: {BLACK: 0, WHITE: 0})
    ply_count: int = 0
    stones_ply: Dict[Tuple[int, int], int] = field(default_factory=dict)
    holes: Set[Tuple[int, int]] = field(default_factory=set)
    hole_forecast: Dict[Tuple[int, int], int] = field(default_factory=dict)
    blipping_stones: Dict[Tuple[int, int], int] = field(default_factory=dict)
    next_star_ply: int = -1
    current_player: int = BLACK
    winner: Optional[int] = None
    last_move: Optional[Tuple[int, int]] = None
    history: List[dict] = field(default_factory=list)
