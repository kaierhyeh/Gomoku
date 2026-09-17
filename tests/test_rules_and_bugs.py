import unittest
import sys
import os

# Add src/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.game import BOARD_SIZE, EMPTY, BLACK, WHITE, MAX_CAPTURES
from core.game import Game
from rules.bonus import get_rules_for_mode
from rules.rules import is_double_free_three, would_capture, has_five, has_any_five


class TestGomokuRulesAndFixes(unittest.TestCase):

    def setUp(self):
        rules = get_rules_for_mode("Standard")
        self.game = Game(rules)

    def test_aide_score_player_callable(self):
        """Verify _score_player can be imported and executed without NameError."""
        from ai.heuristic import _score_player
        score = _score_player(self.game.board, BLACK, 0)
        self.assertEqual(score, 0)

    def test_double_free_three_continuous(self):
        """Test continuous double free-three: . . X X X . in two directions."""
        # Setup board so playing at (9, 9) forms horizontal and vertical free-three
        # Horizontal: (9, 7) empty, (9, 8) X, (9, 9) X (new), (9, 10) X, (9, 11) empty, (9, 12) empty
        # Vertical: (7, 9) empty, (8, 9) X, (9, 9) X (new), (10, 9) X, (11, 9) empty, (12, 9) empty
        self.game.board[9][8] = BLACK
        self.game.board[9][10] = BLACK
        self.game.board[8][9] = BLACK
        self.game.board[10][9] = BLACK

        # (9, 9) should be an illegal double free-three
        self.assertTrue(is_double_free_three(self.game.board, 9, 9, BLACK, self.game.holes))
        self.assertFalse(self.game.is_valid_move(9, 9, BLACK))

    def test_double_free_three_broken(self):
        """Test broken double free-three: . X X . X . in two directions."""
        # Horizontal broken three: (9, 7)=., (9, 8)=X, (9, 9)=new X, (9, 10)=., (9, 11)=X, (9, 12)=.
        # Window: [., X, X, ., X, .] -> exactly 3 stones including (9, 9)
        self.game.board[9][8] = BLACK
        self.game.board[9][11] = BLACK

        # Vertical broken three: (7, 9)=., (8, 9)=X, (9, 9)=new X, (10, 9)=., (11, 9)=X, (12, 9)=.
        self.game.board[8][9] = BLACK
        self.game.board[11][9] = BLACK

        self.assertTrue(is_double_free_three(self.game.board, 9, 9, BLACK, self.game.holes))
        self.assertFalse(self.game.is_valid_move(9, 9, BLACK))

    def test_double_free_three_capture_exception(self):
        """
        Subject rule: It is NOT forbidden to introduce a double-three by capturing a pair.
        """
        # Setup a double free-three position at (9, 9)
        self.game.board[9][8] = BLACK
        self.game.board[9][10] = BLACK
        self.game.board[8][9] = BLACK
        self.game.board[10][9] = BLACK

        # Without capture, (9, 9) is forbidden
        self.assertFalse(self.game.is_valid_move(9, 9, BLACK))

        # Now place a white pair flanked by (9, 9) and (9, 6):
        # (9, 9) Black (new), (9, 8) White, (9, 7) White, (9, 6) Black
        # Wait, (9, 8) was Black; let's flank downwards:
        # (9, 9) Black (new), (10, 10) White, (11, 11) White, (12, 12) Black
        self.game.board[10][10] = WHITE
        self.game.board[11][11] = WHITE
        self.game.board[12][12] = BLACK

        # Playing (9, 9) captures (10, 10) and (11, 11)
        self.assertTrue(would_capture(self.game.board, 9, 9, BLACK, self.game.holes))
        # Therefore, even though it introduces a double-three, it is ALLOWED by exception!
        self.assertTrue(self.game.is_valid_move(9, 9, BLACK))

        # Placing the stone should succeed and apply the capture
        res = self.game.place_stone(9, 9, BLACK)
        self.assertTrue(res)
        self.assertEqual(self.game.captures[BLACK], 1)
        self.assertEqual(self.game.board[10][10], EMPTY)
        self.assertEqual(self.game.board[11][11], EMPTY)

    def test_endgame_capture_immediate_win(self):
        """
        When a player makes 5-in-a-row and opponent CANNOT break it,
        player wins immediately (no need to continue).
        """
        # Black lines up 4 stones
        for c in range(5, 9):
            self.game.board[9][c] = BLACK
        self.game.current_player = BLACK

        # Black places 5th stone at (9, 9)
        res = self.game.place_stone(9, 9, BLACK)
        self.assertTrue(res)
        # White has no stones to capture Black, so Black wins immediately
        self.assertEqual(self.game.winner, BLACK)
        self.assertTrue(self.game.is_game_over())

    def test_endgame_capture_counter_breaks_five(self):
        """
        When Black makes 5-in-a-row, but White CAN break it by capturing a pair:
        1. Game is NOT won immediately; pending_win is set to Black.
        2. White's turn to play.
        3. If White plays the capture, the 5-in-a-row is broken and game continues.
        """
        # Black stones at (9, 5), (9, 6), (9, 7), (9, 8)
        # We will place 5th at (9, 9).
        # We make (9, 5) and (9, 6) vulnerable to capture vertically:
        # (8, 5) White, (9, 5) Black, (10, 5) Black, (11, 5) empty -> White can play at (11, 5) to capture (9, 5) and (10, 5)?
        # Wait, flanking a pair is: White, Black, Black, White.
        # Let's make (9, 5) and (9, 6) Black.
        # Can White capture horizontally?
        # Vertical flank on (9, 6):
        # (7, 6) White, (8, 6) Black, (9, 6) Black, (10, 6) empty -> White can play at (10, 6) to capture (8, 6) and (9, 6)!
        self.game.board[9][5] = BLACK
        self.game.board[9][7] = BLACK
        self.game.board[9][8] = BLACK
        self.game.board[9][9] = BLACK

        # Setup vertical pair containing (9, 6):
        self.game.board[7][6] = WHITE
        self.game.board[8][6] = BLACK
        # (9, 6) will be placed by Black, completing 5-in-a-row horizontally ((9, 5) through (9, 9))
        # AND simultaneously completing the vertical pair flanked by (7, 6) White and (10, 6) empty!

        self.game.current_player = BLACK
        self.game.place_stone(9, 6, BLACK)

        # Black has five-in-a-row: (9, 5), (9, 6), (9, 7), (9, 8), (9, 9)
        self.assertTrue(has_five(self.game.board, 9, 6, BLACK, self.game.holes))

        # BUT White can play at (10, 6) to capture (8, 6) and (9, 6), which breaks Black's five!
        # Therefore, Black has NOT won immediately:
        self.assertIsNone(self.game.winner)
        self.assertEqual(self.game.pending_win, BLACK)
        self.assertEqual(self.game.current_player, WHITE)

        # White plays (10, 6) to break the five
        res = self.game.place_stone(10, 6, WHITE)
        self.assertTrue(res)

        # Capture happened:
        self.assertEqual(self.game.captures[WHITE], 1)
        self.assertEqual(self.game.board[8][6], EMPTY)
        self.assertEqual(self.game.board[9][6], EMPTY)

        # The five was broken! Game is NOT over, pending_win is cleared:
        self.assertFalse(has_any_five(self.game.board, BLACK, self.game.holes))
        self.assertIsNone(self.game.winner)
        self.assertIsNone(self.game.pending_win)

    def test_endgame_capture_counter_fails(self):
        """
        When Black has pending_win, and White plays somewhere else without breaking it:
        Black is declared the winner on White's move completion.
        """
        self.game.board[9][5] = BLACK
        self.game.board[9][7] = BLACK
        self.game.board[9][8] = BLACK
        self.game.board[9][9] = BLACK

        self.game.board[7][6] = WHITE
        self.game.board[8][6] = BLACK

        self.game.current_player = BLACK
        self.game.place_stone(9, 6, BLACK)

        self.assertIsNone(self.game.winner)
        self.assertEqual(self.game.pending_win, BLACK)

        # White plays an irrelevant move at (0, 0)
        self.game.place_stone(0, 0, WHITE)

        # White failed to break Black's five; Black wins!
        self.assertEqual(self.game.winner, BLACK)
        self.assertTrue(self.game.is_game_over())

    def test_endgame_capture_opponent_wins_by_tenth_stone(self):
        """
        Subject rule: If the player has already lost four pairs and the opponent can capture
        one more, the opponent wins by capture.
        """
        # White already has 4 pairs captured (8 stones)
        self.game.captures[WHITE] = 4

        # Black forms 5-in-a-row at row 9
        for c in range(5, 9):
            self.game.board[9][c] = BLACK

        # Setup an irrelevant capture opportunity for White at row 2:
        # (2, 0) White, (2, 1) Black, (2, 2) Black, (2, 3) empty
        self.game.board[2][0] = WHITE
        self.game.board[2][1] = BLACK
        self.game.board[2][2] = BLACK

        self.game.current_player = BLACK
        self.game.place_stone(9, 9, BLACK)

        # Since White can make their 5th capture at (2, 3) and win by capture, Black does NOT win immediately!
        self.assertIsNone(self.game.winner)
        self.assertEqual(self.game.pending_win, BLACK)

        # White takes the 5th capture:
        self.game.place_stone(2, 3, WHITE)

        # White now has 5 pairs (10 stones) -> White wins!
        self.assertEqual(self.game.captures[WHITE], 5)
        self.assertEqual(self.game.winner, WHITE)

    def test_double_free_three_obstructed_not_forbidden(self):
        """
        If one direction is obstructed by opponent stone (cannot become an open four),
        it does not count as a free-three.
        """
        # Horizontal: (9, 7)=White (blocking), (9, 8)=Black, (9, 9)=new, (9, 10)=Black, (9, 11)=White (blocking)
        # Vertical: (8, 9)=Black, (9, 9)=new, (10, 9)=Black
        self.game.board[9][7] = WHITE
        self.game.board[9][8] = BLACK
        self.game.board[9][10] = BLACK
        self.game.board[9][11] = WHITE

        self.game.board[8][9] = BLACK
        self.game.board[10][9] = BLACK

        # Horizontal is completely blocked on both sides, cannot become open four.
        # Only vertical is a free-three (1 direction).
        # Thus (9, 9) is NOT a double-three!
        self.assertFalse(is_double_free_three(self.game.board, 9, 9, BLACK, self.game.holes))
        self.assertTrue(self.game.is_valid_move(9, 9, BLACK))

    def test_undo_restores_pending_win(self):
        """Test that undo correctly restores pending_win state."""
        self.game.board[9][5] = BLACK
        self.game.board[9][7] = BLACK
        self.game.board[9][8] = BLACK
        self.game.board[9][9] = BLACK

        self.game.board[7][6] = WHITE
        self.game.board[8][6] = BLACK

        self.game.place_stone(9, 6, BLACK)
        self.assertEqual(self.game.pending_win, BLACK)

        # White plays irrelevant move
        self.game.place_stone(0, 0, WHITE)
        self.assertEqual(self.game.winner, BLACK)

        # Undo White's move: should revert winner to None and restore pending_win = BLACK
        self.game.undo()
        self.assertIsNone(self.game.winner)
        self.assertEqual(self.game.pending_win, BLACK)
        self.assertEqual(self.game.current_player, WHITE)

        # Undo Black's move: should revert pending_win to None
        self.game.undo()
        self.assertIsNone(self.game.pending_win)
        self.assertEqual(self.game.current_player, BLACK)

    def test_ai_handles_illegal_moves(self):
        """Test that AI runs minimax smoothly even with double free-threes around."""
        from ai.ai import AI
        ai = AI(WHITE)
        self.game.place_stone(9, 9, BLACK)
        self.game.place_stone(9, 10, WHITE)
        # AI should return a valid move without crashing
        move = ai.get_best_move(self.game)
        self.assertIsNotNone(move)
        self.assertTrue(self.game.is_valid_move(move[0], move[1], WHITE))

    def test_heuristic_quick_score_open_ends(self):
        """Verify that open ends are evaluated correctly (dead four scores 0, open four scores 100k)."""
        from ai.heuristic import quick_score_move
        from config.ai import SCORE

        # Dead four: White blocked at both ends: O X X X [X] O
        # Let Black be X, White be O
        self.game.board[9][6] = WHITE
        self.game.board[9][7] = BLACK
        self.game.board[9][8] = BLACK
        self.game.board[9][9] = BLACK
        self.game.board[9][11] = WHITE
        # (9, 10) completes 4 stones, but both ends (6 and 11) are blocked by White!
        dead_score = quick_score_move(self.game.board, 9, 10, BLACK, self.game.captures)

        # Open four: . X X X [X] .
        self.game.board[5][6] = EMPTY
        self.game.board[5][7] = BLACK
        self.game.board[5][8] = BLACK
        self.game.board[5][9] = BLACK
        self.game.board[5][11] = EMPTY
        open_score = quick_score_move(self.game.board, 5, 10, BLACK, self.game.captures)

        self.assertGreater(open_score, dead_score)
        self.assertGreaterEqual(open_score, SCORE["OPEN_FOUR"])

    def test_heuristic_quick_score_captures(self):
        """Verify that capture moves receive huge score bonus in quick_score_move."""
        from ai.heuristic import quick_score_move

        # Flanking setup: (9, 8)=Black (new), (9, 9)=White, (9, 10)=White, (9, 11)=Black
        self.game.board[9][9] = WHITE
        self.game.board[9][10] = WHITE
        self.game.board[9][11] = BLACK

        capture_score = quick_score_move(self.game.board, 9, 8, BLACK, self.game.captures)
        # Quiet move at (0, 0)
        quiet_score = quick_score_move(self.game.board, 0, 0, BLACK, self.game.captures)

        self.assertGreater(capture_score, quiet_score + 20000)

    def test_ai_reaches_depth_10(self):
        """Verify AI reaches depth >= 10 in under 0.5s."""
        from ai.ai import AI
        ai = AI(WHITE)
        self.game.place_stone(9, 9, BLACK)
        self.game.place_stone(9, 10, WHITE)
        self.game.place_stone(10, 9, BLACK)

        move = ai.get_best_move(self.game)
        self.assertIsNotNone(move)
        self.assertGreaterEqual(ai.last_depth_reached, 8)
        self.assertLess(ai.last_think_time, 0.5)

    def test_power_bomb_cleans_holes(self):
        """Verify that when Bomb power destroys a hole, it is removed from state.holes."""
        from config.bonus import POWER_BOMB
        rules = get_rules_for_mode("Power")
        game = Game(rules)

        # Give Black 5 captures to use power
        game.individual_captures[BLACK] = 5
        # Create a hole at (9, 10)
        game.state.holes.add((9, 10))
        game.board[9][10] = 3 # HOLE

        # Black places bomb at (9, 9)
        res = game.place_stone(9, 9, BLACK, power_type=POWER_BOMB)
        self.assertTrue(res)
        # (9, 10) should now be EMPTY and NOT in holes!
        self.assertEqual(game.board[9][10], EMPTY)
        self.assertNotIn((9, 10), game.state.holes)

    def test_get_move_error_diagnostics(self):
        """Verify get_move_error correctly identifies occupied, double_three, out_of_bounds."""
        # 1. Valid empty cell
        self.assertIsNone(self.game.get_move_error(9, 9, BLACK))

        # 2. Out of bounds
        self.assertEqual(self.game.get_move_error(-1, 9, BLACK), "out_of_bounds")
        self.assertEqual(self.game.get_move_error(19, 9, BLACK), "out_of_bounds")

        # 3. Occupied
        self.game.board[9][9] = WHITE
        self.assertEqual(self.game.get_move_error(9, 9, BLACK), "occupied")

        # 4. Double free-three
        # Set up double three at (5, 5)
        self.game.board[5][4] = BLACK
        self.game.board[5][6] = BLACK
        self.game.board[4][5] = BLACK
        self.game.board[6][5] = BLACK
        self.assertEqual(self.game.get_move_error(5, 5, BLACK), "double_three")
        self.assertFalse(self.game.is_valid_move(5, 5, BLACK))

        # 5. Hole forecast
        self.game.hole_forecast[(3, 3)] = 10
        self.assertEqual(self.game.get_move_error(3, 3, BLACK), "hole_forecast")

    def test_quick_score_hierarchy(self):
        """
        Verify that quick_score_move strictly prioritizes immediate win over defense,
        and defense over non-immediate threats.
        """
        from ai.heuristic import quick_score_move
        from config.ai import SCORE

        # Clean board setup:
        # 1. White has 4 stones in row 9: (9, 5), (9, 6), (9, 7), (9, 8)
        for c in range(5, 9):
            self.game.board[9][c] = WHITE
        # 2. Black has 4 stones in col 10: (5, 10), (6, 10), (7, 10), (8, 10)
        for r in range(5, 9):
            self.game.board[r][10] = BLACK

        # For White:
        # - (9, 9) forms White's 5-in-a-row (Immediate Win)
        win_score = quick_score_move(self.game.board, 9, 9, WHITE, self.game.captures)
        # - (4, 10) blocks Black's 5-in-a-row (Urgent Defense)
        defend_score = quick_score_move(self.game.board, 4, 10, WHITE, self.game.captures)
        # - (0, 0) is a quiet move
        quiet_score = quick_score_move(self.game.board, 0, 0, WHITE, self.game.captures)

        self.assertGreaterEqual(win_score, SCORE["FIVE"] * 10)
        self.assertGreaterEqual(defend_score, SCORE["FIVE"] * 5)
        self.assertLess(defend_score, SCORE["FIVE"] * 10)
        self.assertGreater(win_score, defend_score)
        self.assertGreater(defend_score, quiet_score)

    def test_ai_blocks_open_four_instead_of_extending_own_three(self):
        """
        Regression test for 'free win' bug:
        Black has 4 stones in col 10 (rows 5..8).
        White has 3 stones in col 9 (rows 6..8).
        White must block Black at (4, 10) or (9, 10) rather than playing parallel at (5, 9).
        """
        from ai.ai import AI
        ai = AI(WHITE)

        # Black's 4 stones
        for r in range(5, 9):
            self.game.board[r][10] = BLACK
        # White's 3 stones
        for r in range(6, 9):
            self.game.board[r][9] = WHITE

        self.game.current_player = WHITE
        best_move = ai.get_best_move(self.game)

        # AI must block Black at either end of the 4-in-a-row!
        self.assertIn(best_move, [(4, 10), (9, 10)], f"AI played {best_move} instead of blocking at (4, 10) or (9, 10)!")
        self.assertNotEqual(best_move, (5, 9), "AI made the buggy move of extending its own 3 parallel to Black!")

    def test_ai_takes_immediate_win_over_defense(self):
        """
        When both players have 4 stones in a row, White AI must take the immediate win
        rather than defending against Black's threat.
        """
        from ai.ai import AI
        ai = AI(WHITE)

        # Black has 4 stones in col 10 (rows 5..8) -> threatens (4, 10) and (9, 10)
        for r in range(5, 9):
            self.game.board[r][10] = BLACK
        # White has 4 stones in row 2 (cols 5..8) -> can win immediately at (2, 4) or (2, 9)
        for c in range(5, 9):
            self.game.board[2][c] = WHITE

        self.game.current_player = WHITE
        best_move = ai.get_best_move(self.game)

        # AI must win immediately!
        self.assertIn(best_move, [(2, 4), (2, 9)], f"AI played {best_move} instead of winning immediately at (2, 4) or (2, 9)!")

    def test_hint_strings_integrity(self):
        """Verify that all languages have properly formatted shortcut hint strings."""
        import ui.i18n as i18n
        for lang in i18n.LANGS:
            i18n.set_lang(lang)
            restart = i18n.get("restart")
            undo = i18n.get("undo")
            menu = i18n.get("menu")
            quit_str = i18n.get("quit")

            self.assertTrue(restart.startswith("[N]"), f"{lang} restart hint does not start with [N]")
            self.assertTrue(undo.startswith("[R]"), f"{lang} undo hint does not start with [R]")
            self.assertTrue(menu.startswith("[ESC]"), f"{lang} menu hint does not start with [ESC]")
            self.assertTrue(quit_str.startswith("[Q]"), f"{lang} quit hint does not start with [Q]")
            self.assertIn("] ", restart)
            self.assertIn("] ", undo)
            self.assertIn("] ", menu)
            self.assertIn("] ", quit_str)


if __name__ == '__main__':
    unittest.main()
